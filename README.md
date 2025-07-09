🚀 Real-Time Telegram Link Manager Bot
An advanced Telegram Bot powered by Python + Firebase, designed to help you add, categorize, retrieve, and manage content links (like movies, songs, etc.) in real-time with complete control, straight from Telegram!

🔧 Key Features
🔐 Owner-Only Access
Only the authorized admin can use and control the bot functionalities.

➕ Add Links with Structure

📂 First choose Content Type (e.g., Movie, Song)

🗂️ Then provide a Category under it

🔗 Finally, add your link with duplicate-checking.

➕ Add More Links Easily
After every addition, you can instantly add more links under the same category.

📥 Get & Manage Existing Links

Get all content types stored

Select a content type and category

View all links as messages with:

▶️ Play button to open link directly

🗑️ Delete button to remove it from Firebase

❗ Invalid Entry Checks

Invalid content types or categories show friendly error prompts

Re-ask for correct input automatically

❌ Exit Anytime
Dedicated "Exit" button on every flow to return to the main menu.

🧠 State Management
Smart user_state tracking so the bot always knows what step you're on.

🔄 /status Command
Shows real-time bot status and timestamp.

👋 Greet on /start
Time-based welcome greetings like 🌞 Good Morning, 🌇 Good Evening, etc.

🔋 Tech Stack
💬 Telegram Bot API (pyTelegramBotAPI)

☁️ Firebase Realtime Database (for storing links by content type & category)

🌐 Flask (for local testing or later hosting)

🔒 Environment Variables (.env via python-dotenv)

📁 Folder Structure
bash
Copy
Edit
├── app.py                 # Main bot code
├── serviceAccountKey.json # Firebase credentials
├── .env                   # Secrets like BOT_TOKEN, OWNER_ID
🔓 Example Use Case
pgsql
Copy
Edit
1. /start ➝ Choose ➕ Add
2. Enter content type: movie
3. Enter category: thriller
4. Enter link: https://example.com/movie
✅ Bot adds to Firebase, prevents duplicates, and shows "Add more or Exit" option.
🤖 Future Enhancements (Optional)
🔍 Search by keyword in stored links

📊 Analytics dashboard for number of links per category

🔔 Notification on new link addition

👑 Created for Private Use
Made with ❤️ by an Indian Dev for personal media link management over Telegram.
