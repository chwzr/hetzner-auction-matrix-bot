# Hetzner Auction Matrix Bot

This Matrix bot lets users receive notifications when servers matching their specific requirements appear in the Hetzner server auction.

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

## Features Overview

The Matrix bot provides the same functionality as the original Discord version but now works entirely through Matrix protocol, making it suitable for decentralized and privacy-focused environments.

## Requirements

- Python 3.8+
- matrix-nio[e2e] (Matrix client library)
- Motor (Async MongoDB driver)
- Pydantic (for settings management)
- A MongoDB collection named `hetzner` to store user configurations.
- A `.env` file with all the necessary variables (see settings.py).

## Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd hetzner-auction-matrix-bot
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the configuration:**

   Create a `.env` file in the root directory and add the following variables:

   ```env
   MATRIX_HOMESERVER=https://matrix.org
   MATRIX_USERNAME=@your_bot_username:matrix.org
   MATRIX_PASSWORD=your_matrix_bot_password
   MONGODB_URI=your_mongodb_connection_string
   HETZNER_NOTIFICATIONS_ROOM_ID=!your_matrix_room_id:matrix.org
   ```

   You need to create a Matrix account for your bot and get the room ID where you want notifications to be sent.

## Usage

1. **Run the bot:**

   ```bash
   python bot.py
   ```

2. **Available Commands:**

   The bot responds to text commands in Matrix rooms:
   
   - `!hetzner <price> [currency]` - Set up monitoring for servers under the specified price
   - `!help` - Show available commands
   
   Example: `!hetzner 50 EUR` - Monitor for servers under 50 EUR

## How it Works

The bot periodically fetches server auction data from the Hetzner API. It then compares this data against the configurations saved by users in the MongoDB database. If a matching server is found, a notification is sent to the configured Matrix room, mentioning the user who set up the alert.

Configurations are automatically deleted after a notification is sent or if no server has been found within 90 days.

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
