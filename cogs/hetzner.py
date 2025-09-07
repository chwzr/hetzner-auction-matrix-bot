from settings import settings
import asyncio
import datetime


class HetznerMonitor:
    def __init__(self, bot):
        self.bot = bot
        self.monitoring_task = None
        self.running = False

    async def start(self):
        """Start the monitoring task"""
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop the monitoring task"""
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await self.check_auction()
                await asyncio.sleep(31 * 60)  # Wait 31 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def check_auction(self):
        print("Checking Hetzner auction...")

        # Fetch all configs from the database
        configs = await self.bot.db.hetzner.find().to_list(length=None)
        if not configs:
            print("No Hetzner configs found.")
            return
        print(f"Found {len(configs)} Hetzner configs.")

        # Check if we have a room configured for notifications
        if not settings.hetzner_notifications_room_id:
            print("Hetzner auction notifications room not configured.")
            return

        # Fetch the data from Hetzner
        usd_url = (
            "https://www.hetzner.com/_resources/app/data/app/live_data_sb_USD.json"
        )
        eur_url = (
            "https://www.hetzner.com/_resources/app/data/app/live_data_sb_EUR.json"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15"
        }

        usd_request = await self.bot.session.get(usd_url, headers=headers)
        await asyncio.sleep(5)  # Just to be nice to Hetzner
        eur_request = await self.bot.session.get(eur_url, headers=headers)

        if usd_request.status != 200 or eur_request.status != 200:
            print(usd_request.status, await usd_request.text())
            print(eur_request.status, await eur_request.text())
            return

        usd_data = await usd_request.json()
        eur_data = await eur_request.json()

        print("Fetched data from Hetzner.")

        configs_to_delete = []

        # Sift through the configs to find matching servers
        for config in configs:
            currency = config.get("currency", "EUR")

            price = config.get("price", 0)
            vat_percentage = config.get("vat_percentage", 0)

            location = config.get("location", None)

            cpu = config.get("cpu", None)

            ram_size = config.get("ram_size", None)
            ram_ecc = config.get("ram_ecc", None)

            hdd_size = config.get("hdd_size", None)
            hdd_count = config.get("hdd_count", None)
            hdd_type = config.get("hdd_type", None)

            user_id = config.get("user_id", 0)

            data = eur_data
            if currency == "USD":
                data = usd_data

            # compute price_excl only if price_limit is set
            price_excl = price * (1 - vat_percentage / 100)

            # Filter the data based on the user's requirements
            filtered_data = []
            for server in data.get("server", []):
                p = server.get("price", 0)
                dd = server.get("datacenter", "")
                sd = server.get("serverDiskData", {})

                if price_excl and p > price_excl:
                    continue
                if location and location not in dd:
                    continue
                if cpu and cpu not in server.get("cpu", ""):
                    continue
                if ram_size is not None and server.get("ram_size", 0) < ram_size:
                    continue
                if ram_ecc is not None and server.get("is_ecc", False) not in [
                    ram_ecc,
                    True,
                ]:
                    continue
                if hdd_size is not None and server.get("hdd_size", 0) < hdd_size:
                    continue
                if hdd_count is not None and server.get("hdd_count", 0) < hdd_count:
                    continue
                if hdd_type:
                    if not sd.get(hdd_type):
                        continue

                filtered_data.append(server)

            if not filtered_data:
                print(f"No matching servers for user {user_id}.")
                continue
            print(f"Found {len(filtered_data)} matching servers for user {user_id}.")

            # Data for the notification
            filtered_data = filtered_data[0]

            found_url = "https://www.hetzner.com/sb#search=" + str(filtered_data["id"])

            found_location = filtered_data.get("datacenter", "Unknown")
            found_cpu = filtered_data.get("cpu", "Unknown")
            found_ram_size = filtered_data.get("ram_size", 0)
            found_ram_ecc = "ECC" if filtered_data.get("is_ecc", False) else "Non-ECC"
            found_price = filtered_data.get("price", 0) * (1 + vat_percentage / 100)
            found_hdd_size = filtered_data.get("hdd_size", 0)
            found_hdd_count = filtered_data.get("hdd_count", 0)
            found_description = filtered_data.get("description", "Unknown")

            # Format the description
            long_items = [item for item in found_description if len(item) > 10]
            short_items = [item for item in found_description if len(item) <= 10]
            formatted_description = ""
            if long_items:
                formatted_description += "\n".join(long_items) + "\n"
            if short_items:
                formatted_description += " - ".join(short_items)

            # Send notification via Matrix
            server_data = {
                'price': found_price,
                'currency': currency,
                'location': found_location,
                'cpu': found_cpu,
                'ram_size': found_ram_size,
                'ram_ecc': found_ram_ecc,
                'hdd_size': found_hdd_size,
                'hdd_count': found_hdd_count,
                'url': found_url,
                'description': formatted_description
            }
            
            await self.bot.send_notification(user_id, server_data)

            configs_to_delete.append(config.get("_id"))

        print(f"Found {len(configs_to_delete)} matching servers.")

        # Delete configs that have been notified
        if configs_to_delete:
            await self.bot.db.hetzner.delete_many({"_id": {"$in": configs_to_delete}})
            print(f"Deleted {len(configs_to_delete)} configs from the database.")

        # Delete configs older than 90 days
        current_timestamp = int(
            datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
        )
        await self.bot.db.hetzner.delete_many(
            {"timestamp": {"$lt": current_timestamp - 60 * 60 * 24 * 90}}
        )
        print("Deleted configs older than 90 days.")

    async def save_user_config(self, user_id: str, price: int, currency: str = "EUR", 
                              vat_percentage: int = 0, location: str = None, 
                              cpu: str = None, ram_size: int = None, ram_ecc: bool = False,
                              drive_size: int = None, drive_count: int = None, drive_type: str = None):
        """Save a user's Hetzner monitoring configuration"""
        
        # Users can't have more than 10 configs
        user_configs = await self.bot.db.hetzner.count_documents(
            {"user_id": user_id}
        )
        if user_configs >= 10:
            raise ValueError("You can't have more than 10 configs!")

        current_timestamp = int(
            datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
        )

        # Make the config document
        data = {
            "user_id": user_id,
            "timestamp": current_timestamp,
            "currency": currency,
        }
        
        if price > 0:
            data["price"] = price
            if vat_percentage > 0:
                data["vat_percentage"] = vat_percentage
        if location and location != "All Datacenters":
            data["location"] = location
        if cpu and cpu != "Any":
            data["cpu"] = cpu
        if ram_size and ram_size > 32:
            data["ram_size"] = ram_size
        if ram_ecc:
            data["ram_ecc"] = ram_ecc
        if drive_size and drive_size > 256:
            data["hdd_size"] = drive_size
        if drive_count and drive_count > 1:
            data["hdd_count"] = drive_count
        if drive_type and drive_type != "Any":
            data["hdd_type"] = drive_type.lower()
            
        await self.bot.db.hetzner.insert_one(data)
