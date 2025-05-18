# Discord Hetzner Auction Notifications

This Discord bot lets users receive notifications when servers matching their specific requirements appear in the Hetzner server auction.

## Features

- **Customizable Notifications**: Users can specify their desired server specifications, including:
  - CPU
  - RAM (size and ECC support)
  - HDD (size, count, and type)
  - Location
  - Price (with VAT calculation)
  - Currency (EUR or USD)
- **Direct Links**: Notifications include a direct link to the server auction page.
- **Automatic Updates**: The bot periodically checks for new auction items.
- **MongoDB Integration**: User configurations are stored in a MongoDB database.

## Screenshots

![Example notification](/screenshots/example-notification.png)
![Example command](/screenshots/example-command.png)

## Requirements

- Python 3.8+
- discord.py 2.3+
- Motor (Async MongoDB driver)
- Pydantic (for settings management)
- A MongoDB collection named `hetzner` to store user configurations.
- A `.env` file with all the necessary variables (see settings.py).

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Quintenvw/discord-hetzner-auction-notifications
   cd discord-hetzner-auction-notifications
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the configuration:**

   Create a `.env` file in the root directory and add the following variables:

   ```env
   BOT_TOKEN=your_discord_bot_token
   MONGODB_URI=your_mongodb_connection_string
   HETZNER_NOTIFICATIONS_CHANNEL_ID=your_discord_channel_id_for_notifications
   ```

    You can get a Discord bot token from the [Discord developer portal](https://discord.com/developers/applications).

## Usage

1. **Run the bot:**

   ```bash
   python bot.py
   ```

2. **Available Commands:**

   The bot uses slash commands. Use `/hetzner` to save a config and get a notification once it becomes available.

## How it Works

The bot periodically fetches server auction data from the Hetzner API. It then compares this data against the configurations saved by users in the MongoDB database. If a matching server is found, a notification is sent to the configured Discord channel, mentioning the user who set up the alert.

Configurations are automatically deleted after a notification is sent or if no server has been found within 90 days.

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
