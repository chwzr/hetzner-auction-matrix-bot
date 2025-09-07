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
        # Parse command arguments (simplified version)
        parts = message.split()
        if len(parts) < 2:
            await self.client.room_send(
                room.room_id,
                "m.room.message",
                {
                    "msgtype": "m.text",
                    "body": "Usage: !hetzner <price> [currency] [location] [cpu] [ram_size] [options...]"
                }
            )
            return

        try:
            price = int(parts[1])
            currency = parts[2] if len(parts) > 2 else "EUR"
            
            # Save configuration to database
            await self.hetzner_monitor.save_user_config(event.sender, price, currency)
            
            await self.client.room_send(
                room.room_id,
                "m.room.message",
                {
                    "msgtype": "m.text",
                    "body": f"✅ Hetzner monitoring configured! You'll be notified when a server under {price} {currency} becomes available."
                }
            )
        except ValueError:
            await self.client.room_send(
                room.room_id,
                "m.room.message",
                {
                    "msgtype": "m.text",
                    "body": "❌ Invalid price. Please provide a numeric value."
                }
            )

    async def send_help(self, room: MatrixRoom):
        help_text = """
🤖 **Hetzner Auction Bot Commands**

`!hetzner <price> [currency]` - Set up monitoring for Hetzner servers
  - price: Maximum price you want to pay
  - currency: EUR or USD (default: EUR)

`!help` - Show this help message

Example: `!hetzner 50 EUR`
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
