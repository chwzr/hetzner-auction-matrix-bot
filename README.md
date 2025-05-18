# Hetzner Auction Notifications Cog
This Discord cog lets users receive notifications when servers matching their specific requirements appear in the Hetzner server auctions.

## Requirements
- discord.py 2.3+ with app commands support
- A MongoDB collection hetzner to store user configs
- A pydantic settings file with:
- hetzner_notifications_channel_id
- bot.db and bot.session objects
