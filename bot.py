from nio import AsyncClient, MatrixRoom, RoomMessageText
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
import asyncio
from settings import settings
from cogs.hetzner import HetznerMonitor


class MatrixBot:
    def __init__(self):
        self.client = AsyncClient(settings.matrix_homeserver, settings.matrix_username)
        self.session: aiohttp.ClientSession | None = None
        self.db = None
        self.hetzner_monitor = None

    async def setup(self):
        self.session = aiohttp.ClientSession()

        motor = AsyncIOMotorClient(settings.mongodb_uri, connect=True)
        motor.get_io_loop = asyncio.get_running_loop
        self.db = motor.hetzner

        # Initialize Hetzner monitor
        self.hetzner_monitor = HetznerMonitor(self)
        
        # Set up event callbacks
        self.client.add_event_callback(self.message_callback, RoomMessageText)

    async def login(self):
        response = await self.client.login(settings.matrix_password)
        if hasattr(response, 'access_token'):
            print(f"Logged in as {settings.matrix_username}")
            return True
        else:
            print(f"Login failed: {response}")
            return False

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        # Handle incoming messages (commands)
        if event.sender == self.client.user_id:
            return  # Ignore our own messages
            
        message = event.body.strip()
        
        if message.startswith("!hetzner"):
            await self.handle_hetzner_command(room, event, message)
        elif message.startswith("!help"):
            await self.send_help(room)

    async def handle_hetzner_command(self, room: MatrixRoom, event: RoomMessageText, message: str):
        # Parse command arguments with all original Discord parameters
        parts = message.split()
        if len(parts) < 2:
            await self.client.room_send(
                room.room_id,
                "m.room.message",
                {
                    "msgtype": "m.text",
                    "body": "Usage: !hetzner <price> [vat%] [currency] [location] [cpu] [ram_size] [ram_ecc] [drive_size] [drive_count] [drive_type]\n\nExample: !hetzner 50 19 EUR FSN AMD 64 true 1000 2 NVMe\n\nUse !help for detailed parameter information."
                }
            )
            return

        try:
            # Parse parameters with defaults matching the original Discord command
            price = int(parts[1]) if len(parts) > 1 else 0
            vat_percentage = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            currency = parts[3] if len(parts) > 3 and parts[3].upper() in ["EUR", "USD"] else "EUR"
            location = parts[4] if len(parts) > 4 and parts[4] in ["NBG", "FSN", "HEL"] else None
            cpu = parts[5] if len(parts) > 5 and parts[5] in ["AMD", "Intel"] else None
            ram_size = int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else None
            ram_ecc = parts[7].lower() == "true" if len(parts) > 7 else False
            drive_size = int(parts[8]) if len(parts) > 8 and parts[8].isdigit() else None
            drive_count = int(parts[9]) if len(parts) > 9 and parts[9].isdigit() else None
            drive_type = parts[10] if len(parts) > 10 and parts[10] in ["NVMe", "SATA", "HDD"] else None
            
            # Validate ranges (matching original Discord command limits)
            if price < 0 or price > 500:
                raise ValueError("Price must be between 0 and 500")
            if vat_percentage < 0 or vat_percentage > 100:
                raise ValueError("VAT percentage must be between 0 and 100")
            if ram_size and (ram_size < 32 or ram_size > 1024):
                raise ValueError("RAM size must be between 32 and 1024 GB")
            if drive_size and (drive_size < 256 or drive_size > 22528):
                raise ValueError("Drive size must be between 256 and 22528 GB")
            if drive_count and (drive_count < 1 or drive_count > 16):
                raise ValueError("Drive count must be between 1 and 16")
            
            # Save configuration to database
            await self.hetzner_monitor.save_user_config(
                event.sender, price, currency, vat_percentage, location, 
                cpu, ram_size, ram_ecc, drive_size, drive_count, drive_type
            )
            
            # Build confirmation message
            requirements = []
            if price > 0:
                vat_text = f" (incl. {vat_percentage}% VAT)" if vat_percentage > 0 else ""
                requirements.append(f"💰 Max price: {price} {currency}{vat_text}")
            if location:
                requirements.append(f"📍 Location: {location}")
            if cpu:
                requirements.append(f"🖥️ CPU: {cpu}")
            if ram_size:
                ecc_text = " (ECC)" if ram_ecc else ""
                requirements.append(f"💾 RAM: At least {ram_size}GB{ecc_text}")
            if drive_size:
                requirements.append(f"💿 Storage: At least {drive_size}GB")
            if drive_count:
                requirements.append(f"💿 Drive count: At least {drive_count} drives")
            if drive_type:
                requirements.append(f"💿 Drive type: {drive_type}")
            
            requirements_text = "\n".join(requirements) if requirements else "Basic monitoring (any server)"
            
            await self.client.room_send(
                room.room_id,
                "m.room.message",
                {
                    "msgtype": "m.text",
                    "body": f"✅ **Hetzner monitoring configured!**\n\n**Your requirements:**\n{requirements_text}\n\nYou'll be notified when a matching server becomes available."
                }
            )
        except ValueError as e:
            await self.client.room_send(
                room.room_id,
                "m.room.message",
                {
                    "msgtype": "m.text",
                    "body": f"❌ **Error:** {str(e)}\n\nUse !help for parameter information."
                }
            )
        except Exception as e:
            await self.client.room_send(
                room.room_id,
                "m.room.message",
                {
                    "msgtype": "m.text",
                    "body": f"❌ **Error saving configuration:** {str(e)}"
                }
            )

    async def send_help(self, room: MatrixRoom):
        help_text = """
🤖 **Hetzner Auction Bot Commands**

**Main Command:**
`!hetzner <price> [vat%] [currency] [location] [cpu] [ram_size] [ram_ecc] [drive_size] [drive_count] [drive_type]`

**Parameters (all optional except price):**
• **price** (0-500): Maximum price you want to pay
• **vat%** (0-100): VAT percentage you pay (default: 0)
• **currency**: EUR or USD (default: EUR)
• **location**: NBG, FSN, or HEL (default: any)
• **cpu**: AMD or Intel (default: any)
• **ram_size** (32-1024): Minimum RAM in GB (default: any)
• **ram_ecc**: true or false - ECC RAM required (default: false)
• **drive_size** (256-22528): Minimum drive size in GB (default: any)
• **drive_count** (1-16): Minimum number of drives (default: any)
• **drive_type**: NVMe, SATA, or HDD (default: any)

**Other Commands:**
• `!help` - Show this help message

**Examples:**
• `!hetzner 50` - Monitor servers under 50 EUR
• `!hetzner 100 19 EUR FSN AMD` - Under 100 EUR (incl. 19% VAT), in Frankfurt, AMD CPU
• `!hetzner 75 0 USD NBG Intel 64 true 1000 2 NVMe` - Full specification example

**Notes:**
- You can have up to 10 active configurations
- Configurations expire after 90 days
- All parameters after price are optional and positional
        """
        await self.client.room_send(
            room.room_id,
            "m.room.message",
            {
                "msgtype": "m.text",
                "body": help_text.strip()
            }
        )

    async def send_notification(self, user_id: str, server_data: dict):
        """Send notification to the configured room"""
        room_id = settings.hetzner_notifications_room_id
        
        message = f"""
🚨 **Server Found for {user_id}!**

💰 **Price**: {server_data['price']} {server_data['currency']}
📍 **Location**: {server_data['location']}
🖥️ **CPU**: {server_data['cpu']}
💾 **RAM**: {server_data['ram_size']} GB ({server_data['ram_ecc']})
💿 **Storage**: {server_data['hdd_size']} GB ({server_data['hdd_count']} drives)

🔗 **View Server**: {server_data['url']}

{server_data['description']}
        """
        
        await self.client.room_send(
            room_id,
            "m.room.message",
            {
                "msgtype": "m.text",
                "body": message.strip()
            }
        )

    async def close(self):
        if self.hetzner_monitor:
            await self.hetzner_monitor.stop()
        if self.session:
            await self.session.close()
        await self.client.close()


async def main():
    bot = MatrixBot()
    
    try:
        await bot.setup()
        
        if not await bot.login():
            print("Failed to login to Matrix")
            return
            
        # Start the Hetzner monitoring task
        await bot.hetzner_monitor.start()
        
        # Start syncing with the server
        await bot.client.sync_forever(timeout=30000)
        
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Bot error: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
