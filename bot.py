import asyncio
import logging
import random
import os
import json
import sys
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import InputReportReasonPersonalDetails
from datetime import datetime

# Настройки
API_ID = 35546672  # Замени на свой API ID
API_HASH = 'd6d01041a3dddd8220b571f419921e3b'  # Замени на свой API Hash
BOT_TOKEN = '8519358318:AAHqz_2uAP4X4l3c7rr6Ic0GDoKFiZrw84k'  # Токен бота
OWNER_ID = 8364709627  # Твой ID

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXTS_DIR = os.path.join(BASE_DIR, 'texts')
SESSIONS_DIR = os.path.join(BASE_DIR, 'sessions')
os.makedirs(TEXTS_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Disable logs
logging.basicConfig(level=logging.WARNING)

# ========== LOAD DATA ==========

def load_complaints():
    """Load complaints from file"""
    filepath = os.path.join(TEXTS_DIR, 'Personal_data.txt')
    complaints = []
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            complaints = lines
            print(f"[OK] Loaded {len(lines)} complaints")
    else:
        print(f"[ERROR] File not found: Personal_data.txt")
        complaints = [
            "This bot offers illegal personal data search services ('probyv'). This violates Telegram Terms of Service section 8.2.",
            "Bot provides unauthorized access to personal information without consent. This is against Telegram rules.",
            "Report: Bot engages in collection and distribution of personal data. Request immediate ban."
        ]
    
    return complaints

COMPLAINTS = load_complaints()

def load_sessions():
    sessions = {}
    try:
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(SESSIONS_DIR, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    session_id = data['session_id']
                    sessions[session_id] = data
    except:
        pass
    return sessions

def save_session(session_id, session_data):
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(filepath, 'w') as f:
        json.dump(session_data, f, indent=2)

def delete_session(session_id):
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)

# Global data
sessions_db = load_sessions()
active_clients = {}
user_states = {}

print(f"\n{'='*50}")
print("PERSONAL DATA REPORT BOT")
print(f"Owner: {OWNER_ID}")
print(f"Sessions: {len(sessions_db)}")
print(f"Complaints: {len(COMPLAINTS)}")
print(f"{'='*50}\n")

# ========== BOT CLIENT ==========
bot = TelegramClient(
    session='bot_session',
    api_id=API_ID,
    api_hash=API_HASH
)

# ========== KEYBOARDS ==========

def main_menu():
    return [
        [Button.inline("ADD SESSION", b"add_session"),
         Button.inline("LIST SESSIONS", b"list_sessions")],
        [Button.inline("SEND REPORTS", b"send_reports")],
        [Button.inline("STATS", b"stats"),
         Button.inline("DELETE", b"delete_sessions")],
        [Button.inline("STOP ALL", b"stop_all")]
    ]

def back_button():
    return [[Button.inline("BACK", b"back_main")]]

def cancel_button():
    return [[Button.inline("CANCEL", b"cancel")]]

# ========== EVENT HANDLERS ==========

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.sender_id != OWNER_ID:
        await event.reply("ACCESS DENIED")
        return
    
    text = (
        "PERSONAL DATA REPORT BOT\n\n"
        "Sends official Telegram reports.\n"
        "Only personal data violations.\n\n"
        "Use buttons below:"
    )
    
    await event.reply(text, buttons=main_menu())

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    if event.sender_id != OWNER_ID:
        await event.answer("ACCESS DENIED", alert=True)
        return
    
    data = event.data.decode('utf-8')
    
    try:
        if data == "back_main":
            await event.edit("MAIN MENU", buttons=main_menu())
        
        elif data == "add_session":
            await event.edit(
                "ADD SESSION\n\n"
                "Choose method:",
                buttons=[
                    [Button.inline("PHONE + API", b"auth_phone")],
                    [Button.inline("SESSION STRING", b"auth_string")],
                    [Button.inline("BACK", b"back_main")]
                ]
            )
        
        elif data == "auth_phone":
            user_states[event.sender_id] = {'state': 'waiting_phone'}
            await event.edit(
                "SEND PHONE NUMBER\n\n"
                "Format: +79123456789\n\n"
                "Press Cancel to stop:",
                buttons=cancel_button()
            )
        
        elif data == "auth_string":
            user_states[event.sender_id] = {'state': 'waiting_string'}
            await event.edit(
                "SEND SESSION STRING\n\n"
                "From @ScarpyRobot\n\n"
                "Format: session_string",
                buttons=cancel_button()
            )
        
        elif data == "list_sessions":
            if not sessions_db:
                await event.edit("NO SESSIONS", buttons=main_menu())
                return
            
            text = "SESSIONS:\n\n"
            for session_id, data in sessions_db.items():
                status = "ONLINE" if session_id in active_clients else "OFFLINE"
                text += f"[{status}] #{session_id}\n"
                text += f"User: {data.get('username', 'None')}\n"
                text += f"Phone: {data.get('phone', 'Unknown')}\n\n"
            
            text += f"Total: {len(sessions_db)}"
            
            await event.edit(text, buttons=back_button())
        
        elif data == "send_reports":
            await event.edit(
                "SEND REPORTS\n\n"
                "Send @username of target bot:",
                buttons=cancel_button()
            )
            user_states[event.sender_id] = {'state': 'waiting_target'}
        
        elif data == "stats":
            online = len([c for c in active_clients.values() if c.is_connected()])
            
            stats_text = (
                f"STATISTICS\n\n"
                f"Owner: {OWNER_ID}\n"
                f"Sessions: {len(sessions_db)}\n"
                f"Online: {online}\n"
                f"Complaints: {len(COMPLAINTS)}\n\n"
                f"Folders:\n"
                f"sessions/\n"
                f"texts/"
            )
            
            await event.edit(stats_text, buttons=back_button())
        
        elif data == "delete_sessions":
            if not sessions_db:
                await event.edit("NO SESSIONS", buttons=main_menu())
                return
            
            buttons = []
            for session_id in sessions_db.keys():
                buttons.append([Button.inline(f"DELETE #{session_id}", f"delete_{session_id}".encode())])
            buttons.append([Button.inline("BACK", b"back_main")])
            
            await event.edit(
                "DELETE SESSION:\n\n"
                "Click to delete:",
                buttons=buttons
            )
        
        elif data.startswith("delete_"):
            session_id = data.replace("delete_", "")
            
            if session_id in sessions_db:
                if session_id in active_clients:
                    try:
                        await active_clients[session_id].disconnect()
                    except:
                        pass
                    del active_clients[session_id]
                
                delete_session(session_id)
                del sessions_db[session_id]
                
                await event.answer(f"DELETED #{session_id}", alert=True)
                
                if sessions_db:
                    buttons = []
                    for sid in sessions_db.keys():
                        buttons.append([Button.inline(f"DELETE #{sid}", f"delete_{sid}".encode())])
                    buttons.append([Button.inline("BACK", b"back_main")])
                    
                    await event.edit(
                        "DELETE SESSION:\n\n"
                        "Click to delete:",
                        buttons=buttons
                    )
                else:
                    await event.edit("ALL DELETED", buttons=main_menu())
            else:
                await event.answer("NOT FOUND", alert=True)
        
        elif data == "stop_all":
            count = 0
            for client in list(active_clients.values()):
                try:
                    await client.disconnect()
                    count += 1
                except:
                    pass
            
            active_clients.clear()
            await event.edit(f"STOPPED {count}", buttons=main_menu())
        
        elif data == "cancel":
            if event.sender_id in user_states:
                del user_states[event.sender_id]
            await event.edit("CANCELLED", buttons=main_menu())
    
    except Exception as e:
        await event.answer(f"ERROR: {str(e)[:100]}", alert=True)

# ========== MESSAGE HANDLERS ==========

@bot.on(events.NewMessage)
async def message_handler(event):
    if event.sender_id != OWNER_ID:
        return
    
    user_id = event.sender_id
    text = event.text.strip()
    
    if user_id not in user_states:
        return
    
    state_data = user_states[user_id]
    state = state_data.get('state')
    
    try:
        # Phone auth
        if state == 'waiting_phone':
            if not text.startswith('+'):
                await event.reply("WRONG FORMAT. Use +79123456789", buttons=cancel_button())
                return
            
            phone = text
            state_data['phone'] = phone
            state_data['api_id'] = None
            state_data['api_hash'] = None
            
            await event.reply(
                f"PHONE: {phone}\n\n"
                "Now send API_ID and API_HASH:\n"
                "Format: API_ID API_HASH\n\n"
                "Get from: https://my.telegram.org",
                buttons=cancel_button()
            )
            
            state_data['state'] = 'waiting_api'
        
        # API data
        elif state == 'waiting_api':
            phone = state_data.get('phone')
            if not phone:
                del user_states[user_id]
                await event.reply("ERROR: No phone", buttons=main_menu())
                return
            
            parts = text.split()
            if len(parts) < 2:
                await event.reply("WRONG FORMAT", buttons=cancel_button())
                return
            
            try:
                user_api_id = int(parts[0])
                user_api_hash = parts[1]
            except:
                await event.reply("INVALID API", buttons=cancel_button())
                return
            
            # Save API
            state_data['api_id'] = user_api_id
            state_data['api_hash'] = user_api_hash
            
            # Create client
            temp_client = TelegramClient(
                StringSession(),
                user_api_id,
                user_api_hash
            )
            
            try:
                await temp_client.connect()
                
                # Request code
                sent_code = await temp_client.send_code_request(phone)
                
                state_data['phone_code_hash'] = sent_code.phone_code_hash
                state_data['client'] = temp_client  # Save client for later
                state_data['state'] = 'waiting_code'
                
                await event.reply(
                    f"✅ CODE SENT TO {phone}\n\n"
                    "📲 Send SMS code (5 digits):\n"
                    "⚠️ Code expires in 5 minutes!",
                    buttons=cancel_button()
                )
                
            except Exception as e:
                try:
                    await temp_client.disconnect()
                except:
                    pass
                if 'client' in state_data:
                    del state_data['client']
                await event.reply(f"ERROR: {str(e)}", buttons=main_menu())
        
        # SMS code
        elif state == 'waiting_code':
            if not text.replace('-', '').isdigit():  # Allow codes like 12-345
                await event.reply("DIGITS ONLY (like 12345 or 12-345)", buttons=cancel_button())
                return
            
            # Clean code (remove dashes)
            code = text.replace('-', '')
            
            phone = state_data.get('phone')
            api_id = state_data.get('api_id')
            api_hash = state_data.get('api_hash')
            phone_code_hash = state_data.get('phone_code_hash')
            temp_client = state_data.get('client')
            
            if not all([phone, api_id, api_hash, phone_code_hash]):
                del user_states[user_id]
                await event.reply("DATA ERROR", buttons=main_menu())
                return
            
            try:
                if temp_client is None:
                    # Recreate client if needed
                    temp_client = TelegramClient(
                        StringSession(),
                        api_id,
                        api_hash
                    )
                    await temp_client.connect()
                
                # Try to sign in with code
                try:
                    await temp_client.sign_in(
                        phone=phone,
                        code=code,
                        phone_code_hash=phone_code_hash
                    )
                except Exception as signin_error:
                    # If code expired, request new one
                    if "expired" in str(signin_error).lower():
                        await event.reply(
                            "⏰ Code expired! Requesting new code...",
                            buttons=cancel_button()
                        )
                        
                        # Request new code
                        sent_code = await temp_client.send_code_request(phone)
                        state_data['phone_code_hash'] = sent_code.phone_code_hash
                        
                        await event.reply(
                            f"✅ NEW CODE SENT TO {phone}\n\n"
                            "📲 Send new SMS code:",
                            buttons=cancel_button()
                        )
                        return
                    else:
                        raise signin_error
                
                # Get session
                session_string = temp_client.session.save()
                me = await temp_client.get_me()
                
                # Save session
                session_id = f"s{len(sessions_db) + 1:03d}"
                
                session_data = {
                    'session_id': session_id,
                    'session_string': session_string,
                    'phone': phone,
                    'username': me.username or 'None',
                    'user_id': me.id,
                    'api_id': api_id,
                    'api_hash': api_hash
                }
                
                sessions_db[session_id] = session_data
                save_session(session_id, session_data)
                
                await event.reply(
                    f"✅ SESSION ADDED\n\n"
                    f"🆔 ID: #{session_id}\n"
                    f"👤 User: @{me.username or 'none'}\n"
                    f"📱 Phone: {phone}\n"
                    f"🆔 User ID: {me.id}",
                    buttons=main_menu()
                )
                
                await temp_client.disconnect()
                if 'client' in state_data:
                    del state_data['client']
                del user_states[user_id]
                
            except Exception as e:
                try:
                    await temp_client.disconnect()
                except:
                    pass
                if 'client' in state_data:
                    del state_data['client']
                del user_states[user_id]
                
                error_msg = str(e)
                if "expired" in error_msg.lower():
                    await event.reply(
                        "⏰ Code expired!\n\n"
                        "Start over with /start and ADD SESSION",
                        buttons=main_menu()
                    )
                elif "code" in error_msg.lower():
                    await event.reply(
                        f"❌ WRONG CODE: {error_msg}\n\n"
                        "Start over with /start",
                        buttons=main_menu()
                    )
                else:
                    await event.reply(f"❌ AUTH ERROR: {error_msg}", buttons=main_menu())
        
        # Session string
        elif state == 'waiting_string':
            if len(text) < 50:
                await event.reply("TOO SHORT", buttons=cancel_button())
                return
            
            session_string = text
            
            # Try with main API
            temp_client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            
            try:
                await temp_client.connect()
                
                if not await temp_client.is_user_authorized():
                    await temp_client.disconnect()
                    await event.reply(
                        "Need API for this session.\n\n"
                        "Send API_ID API_HASH:",
                        buttons=cancel_button()
                    )
                    state_data['session_string'] = session_string
                    state_data['state'] = 'waiting_string_api'
                    return
                
                me = await temp_client.get_me()
                
                session_id = f"s{len(sessions_db) + 1:03d}"
                
                session_data = {
                    'session_id': session_id,
                    'session_string': session_string,
                    'phone': me.phone or 'Unknown',
                    'username': me.username or 'None',
                    'user_id': me.id,
                    'api_id': API_ID,
                    'api_hash': API_HASH
                }
                
                sessions_db[session_id] = session_data
                save_session(session_id, session_data)
                
                await event.reply(
                    f"SESSION ADDED\n\n"
                    f"ID: #{session_id}\n"
                    f"User: @{me.username or 'none'}",
                    buttons=main_menu()
                )
                
                await temp_client.disconnect()
                del user_states[user_id]
                
            except Exception as e:
                try:
                    await temp_client.disconnect()
                except:
                    pass
                await event.reply(f"ERROR: {str(e)}", buttons=main_menu())
                del user_states[user_id]
        
        # Session string with API
        elif state == 'waiting_string_api':
            session_string = state_data.get('session_string')
            if not session_string:
                del user_states[user_id]
                await event.reply("ERROR", buttons=main_menu())
                return
            
            parts = text.split()
            if len(parts) < 2:
                await event.reply("WRONG FORMAT", buttons=cancel_button())
                return
            
            try:
                user_api_id = int(parts[0])
                user_api_hash = parts[1]
            except:
                await event.reply("INVALID API", buttons=cancel_button())
                return
            
            temp_client = TelegramClient(
                StringSession(session_string),
                user_api_id,
                user_api_hash
            )
            
            try:
                await temp_client.connect()
                
                if not await temp_client.is_user_authorized():
                    await temp_client.disconnect()
                    await event.reply("NOT AUTHORIZED", buttons=main_menu())
                    del user_states[user_id]
                    return
                
                me = await temp_client.get_me()
                
                session_id = f"s{len(sessions_db) + 1:03d}"
                
                session_data = {
                    'session_id': session_id,
                    'session_string': session_string,
                    'phone': me.phone or 'Unknown',
                    'username': me.username or 'None',
                    'user_id': me.id,
                    'api_id': user_api_id,
                    'api_hash': user_api_hash
                }
                
                sessions_db[session_id] = session_data
                save_session(session_id, session_data)
                
                await event.reply(
                    f"SESSION ADDED\n\n"
                    f"ID: #{session_id}\n"
                    f"User: @{me.username or 'none'}",
                    buttons=main_menu()
                )
                
                await temp_client.disconnect()
                del user_states[user_id]
                
            except Exception as e:
                try:
                    await temp_client.disconnect()
                except:
                    pass
                await event.reply(f"ERROR: {str(e)}", buttons=main_menu())
                del user_states[user_id]
        
        # Target
        elif state == 'waiting_target':
            if not text:
                await event.reply("ENTER USERNAME", buttons=cancel_button())
                return
            
            target_bot = text if text.startswith('@') else f'@{text}'
            await start_reports(event, target_bot)
            del user_states[user_id]
    
    except Exception as e:
        if user_id in user_states:
            del user_states[user_id]
        await event.reply(f"ERROR: {str(e)}", buttons=main_menu())

# ========== REPORT FUNCTIONS ==========

async def get_client(session_id):
    if session_id not in sessions_db:
        return None
    
    try:
        if session_id in active_clients:
            client = active_clients[session_id]
            if client.is_connected():
                return client
            else:
                del active_clients[session_id]
        
        session_data = sessions_db[session_id]
        session_string = session_data['session_string']
        api_id = session_data.get('api_id', API_ID)
        api_hash = session_data.get('api_hash', API_HASH)
        
        client = TelegramClient(
            StringSession(session_string),
            api_id,
            api_hash
        )
        
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.disconnect()
            return None
        
        active_clients[session_id] = client
        return client
        
    except Exception as e:
        print(f"[{session_id}] Client error: {e}")
        return None

async def send_report(session_id, target_bot):
    """Send report to Telegram support - ТОЛЬКО Personal Data"""
    if not COMPLAINTS:
        return False, "NO COMPLAINTS"
    
    client = await get_client(session_id)
    if not client:
        return False, "NO CLIENT"
    
    try:
        # Get target
        try:
            entity = await client.get_entity(target_bot)
        except Exception as e:
            return False, f"TARGET ERROR: {str(e)[:30]}"
        
        # Get messages for report
        message_ids = []
        try:
            messages = await client.get_messages(entity, limit=3)
            for msg in messages:
                if hasattr(msg, 'id'):
                    message_ids.append(msg.id)
        except:
            pass
        
        # Если нет сообщений, используем пустой список
        if not message_ids:
            message_ids = []
        
        # Берем случайный текст из файла Personal_data.txt
        complaint = random.choice(COMPLAINTS)
        
        # ТОЛЬКО Personal Data репорт
        try:
            reason = InputReportReasonPersonalDetails()
            
            # Отправляем репорт - ИСПРАВЛЕННЫЙ СИНТАКСИС
            # В некоторых версиях Telethon требуется параметр 'message'
            result = await client(ReportRequest(
                peer=entity,
                id=message_ids,
                reason=reason,
                message=complaint[:200]  # Добавляем текст сообщения
            ))
            
            print(f"[{session_id}] Personal Data Report sent: {complaint[:50]}...")
            return True, f"PERSONAL DATA REPORT ({len(message_ids)} messages)"
            
        except Exception as e:
            print(f"[{session_id}] Report failed: {e}")
            
            # Попробуем альтернативный синтаксис
            try:
                # Если первый метод не сработал, пробуем без message
                result = await client(ReportRequest(
                    peer=entity,
                    id=message_ids,
                    reason=reason
                ))
                print(f"[{session_id}] Personal Data Report sent (without message)")
                return True, f"PERSONAL DATA REPORT ({len(message_ids)} messages)"
            except Exception as e2:
                print(f"[{session_id}] Alternative method also failed: {e2}")
                return False, f"REPORT FAILED: {str(e2)[:30]}"
        
    except Exception as e:
        if session_id in active_clients:
            try:
                await active_clients[session_id].disconnect()
            except:
                pass
            del active_clients[session_id]
        
        return False, f"ERROR: {str(e)[:30]}"

async def start_reports(event, target_bot):
    if not sessions_db:
        await event.reply("NO SESSIONS", buttons=main_menu())
        return
    
    start_msg = await event.reply(
        f"🚀 STARTING PERSONAL DATA REPORTS\n\n"
        f"🎯 Target: {target_bot}\n"
        f"👥 Sessions: {len(sessions_db)}\n"
        f"📝 Complaints: {len(COMPLAINTS)}\n"
        f"⏳ Status: Preparing..."
    )
    
    results = []
    success = 0
    
    for idx, session_id in enumerate(sorted(sessions_db.keys()), 1):
        try:
            # Update progress
            if idx % 2 == 0 or idx == len(sessions_db):
                await start_msg.edit(
                    f"📤 SENDING PERSONAL DATA REPORTS\n\n"
                    f"🎯 Target: {target_bot}\n"
                    f"📊 Progress: {idx}/{len(sessions_db)}\n"
                    f"✅ Success: {success}\n"
                    f"🔄 Current: #{session_id}"
                )
            
            # Send report
            ok, result_msg = await send_report(session_id, target_bot)
            
            if ok:
                results.append(f"✅ #{session_id} - {result_msg}")
                success += 1
            else:
                results.append(f"❌ #{session_id} - {result_msg}")
            
            print(f"[{session_id}] {'OK' if ok else 'FAIL'} - {result_msg}")
            
            # Delay between reports
            if idx < len(sessions_db):
                delay = random.uniform(5, 15)  # Увеличенная задержка
                await asyncio.sleep(delay)
                
        except Exception as e:
            results.append(f"❌ #{session_id} - ERROR: {str(e)[:30]}")
            print(f"[{session_id}] ERROR: {e}")
    
    # Final report
    report_lines = [
        f"📊 PERSONAL DATA REPORTS COMPLETED",
        f"",
        f"🎯 Target: {target_bot}",
        f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}",
        f"",
        f"✅ Successful: {success}",
        f"❌ Failed: {len(sessions_db) - success}",
        f"📊 Total sessions: {len(sessions_db)}",
        f"📝 Complaints used: {len(COMPLAINTS)}",
        f"",
        f"📋 Results:"
    ]
    
    # Показываем первые 10 результатов
    for result in results[:10]:
        report_lines.append(result)
    
    if len(results) > 10:
        report_lines.append(f"... and {len(results) - 10} more")
    
    await start_msg.edit(
        "\n".join(report_lines),
        buttons=[
            [Button.inline("🔄 SEND AGAIN", b"send_reports")],
            [Button.inline("📋 MENU", b"back_main")]
        ]
    )
    
    # Save report to file
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"report_{timestamp}.txt", 'w', encoding='utf-8') as f:
            f.write(f"Personal Data Report {timestamp}\n")
            f.write(f"Target: {target_bot}\n")
            f.write(f"Successful: {success}/{len(sessions_db)}\n")
            f.write(f"Complaints from file: {len(COMPLAINTS)}\n")
            f.write(f"Example complaint: {random.choice(COMPLAINTS)[:100]}\n\n")
            f.write("Results:\n")
            for result in results:
                f.write(f"{result}\n")
        print(f"📁 Report saved to report_{timestamp}.txt")
    except Exception as e:
        print(f"❌ Error saving report: {e}")

# ========== MAIN ==========

async def main():
    print("🚀 Starting Personal Data Report Bot...")
    print(f"📂 Complaints loaded from Personal_data.txt: {len(COMPLAINTS)}")
    
    try:
        await bot.start(bot_token=BOT_TOKEN)
        
        print("=" * 50)
        print("✅ BOT STARTED")
        print(f"👑 Owner: {OWNER_ID}")
        print(f"👥 Sessions: {len(sessions_db)}")
        print(f"📝 Complaints: {len(COMPLAINTS)}")
        print("=" * 50)
        print("\n📩 Send /start to bot")
        print("⏳ Waiting for commands...\n")
        
        await bot.run_until_disconnected()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        print("\n🧹 Cleaning up...")
        for client in active_clients.values():
            try:
                await client.disconnect()
            except:
                pass
        print("✅ Bot stopped")

# ========== ENTRY POINT ==========
if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped")