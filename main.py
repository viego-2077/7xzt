import discord
import asyncio
import time
import os
import re


TOKEN = os.getenv("TOKEN")

# Khởi tạo client selfbot với intents đầy đủ
client = discord.Client()


chui_task = None
spamming = False
auto_react_targets = {}  # {user_id: emoji}
_spam_task = None

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")


@client.event
async def on_message(message):
    global spamming, auto_react_targets, chui_task, _spam_task  # 🛠 Chỉ khai báo ở đây

    # React tự động với mọi tin nhắn (kể cả chính bạn)
    if message.author.id in auto_react_targets:
        try:
            await message.add_reaction(auto_react_targets[message.author.id])
        except Exception as e:
            print(f"Lỗi khi react: {e}")

    # Chỉ xử lý lệnh nếu là tin nhắn từ chính bạn
    if message.author.id != client.user.id:
        return


    # ------- Các lệnh từ selfbot chính mình -------
#lenh ;create
    if message.content.startswith(";create "):
        try:
            args = message.content[len(";create "):].split("-")
            if len(args) != 3:
                await message.channel.send("❌ Cú pháp: `;create <server_id>-<tên_kênh>-<số_lượng>`")
                return

            guild_id = int(args[0])
            channel_name = args[1]
            count = int(args[2])

            guild = client.get_guild(guild_id)
            if not guild:
                await message.channel.send("⚠️ Không tìm thấy server.")
                return

            # Tạo thư mục nếu chưa có
            if not os.path.exists("webhook"):
                os.makedirs("webhook")

            # Làm sạch tên server để dùng làm tên file
            safe_guild_name = re.sub(r'[\\/*?:"<>|]', "_", guild.name)
            file_path = f"webhook/{safe_guild_name}.txt"

            webhook_links = []
            for i in range(count):
                ch = await guild.create_text_channel(name=f"{channel_name}-{i + 1}")
                wh = await ch.create_webhook(name=f"{channel_name}-webhook")
                webhook_links.append(f"{ch.name}: {wh.url}")

            # Ghi các link webhook vào file
            with open(file_path, "a", encoding="utf-8") as f:  # "a" để ghi nối tiếp
                f.write("\n".join(webhook_links) + "\n")


        except Exception as e:
            await message.channel.send(f"❌ Lỗi: {e}")

    # ;del <server_id>
    elif message.content.startswith(";del "):
        try:
            guild_id = int(message.content.split(" ")[1])
            guild = client.get_guild(guild_id)
            if not guild:
                await message.channel.send("⚠️ Không tìm thấy server.")
                return

            count = 0
            for ch in guild.channels:
                try:
                    await ch.delete()
                    count += 1
                except:
                    pass
            await message.channel.send(f"✅ Đã xoá {count} kênh.")
        except Exception as e:
            await message.channel.send(f"❌ Lỗi khi xoá: {e}")

    # ;wh <server_id> <tên_webhook>
    elif message.content.startswith(";wh "):
        try:
            args = message.content.split(" ", 2)
            if len(args) < 3:
                await message.channel.send("❌ Cú pháp: `;wh <server_id> <tên_webhook>`")
                return

            guild_id = int(args[1])
            name = args[2]
            guild = client.get_guild(guild_id)
            if not guild:
                await message.channel.send("⚠️ Không tìm thấy server.")
                return

            # Tạo thư mục nếu chưa tồn tại
            if not os.path.exists("webhook"):
                os.makedirs("webhook")

            # Làm sạch tên server để dùng làm tên file
            safe_guild_name = re.sub(r'[\\/*?:"<>|]', "_", guild.name)
            file_path = f"webhook/{safe_guild_name}.txt"

            webhook_links = []
            success = 0
            for ch in guild.text_channels:
                try:
                    wh = await ch.create_webhook(name=name)
                    webhook_links.append(f"{ch.name}: {wh.url}")
                    success += 1
                except:
                    pass

            # Ghi các link webhook vào file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(webhook_links))

            await message.channel.send(
                f"✅"
            )
        except Exception as e:
            await message.channel.send(f"❌ Lỗi: {e}")

    # ;stop
    elif message.content.strip() == ";stop":
        spamming = False
        await message.channel.send("🛑 Đã dừng spam.")

    # ;ar <@user> <emoji>
    elif message.content.startswith(";ar "):
        try:
            parts = message.content.split(" ")
            if len(parts) < 3:
                await message.channel.send("❌ Cú pháp: `;ar <@user> <emoji>`")
                return
            mention = parts[1]
            emoji = parts[2]
            user_id = int(mention.replace("<@", "").replace("!", "").replace(">", ""))
            auto_react_targets[user_id] = emoji
            await message.channel.send(f"✅ Auto-react <@{user_id}> emoji {emoji}")
            await asyncio.sleep(3)
            await message.delete()
        except Exception as e:
            await message.channel.send(f"❌ Lỗi: {e}")

    # ;ur — xoá toàn bộ auto-react
    elif message.content.strip() == ";ur":
        auto_react_targets.clear()
        await message.channel.send("done")
        await asyncio.sleep(3)
        await message.delete()

    # ;av <@user> — hiện avatar của người được tag hoặc chính mình
    elif message.content.startswith(";av"):
        try:
            if message.mentions:
                user = message.mentions[0]
            else:
                user = message.author  # nếu không tag ai → chính mình

            avatar_url = user.display_avatar.url  # full-size avatar (GIF nếu có)
            await message.channel.send(
                f"{user.mention} Avatar:\n{avatar_url}",
                delete_after=10
            )
            await message.delete()

        except Exception as e:
            await message.channel.send(f"❌ Lỗi: {e}", delete_after=5)
            await message.delete()

    # ;ping — đo độ trễ
    elif message.content.strip() == ";ping":
        try:
            start = time.perf_counter()
            msg = await message.channel.send("chờ chút...")
            end = time.perf_counter()
            latency = (end - start) * 1000  # chuyển sang mili giây

            await msg.edit(content=f"🏓 Pong! `{int(latency)}ms`")
            await message.delete()
        except Exception as e:
            await message.channel.send(f"❌ Lỗi khi đo ping: {e}", delete_after=5)
            await message.delete()

    # ;chui <delay_ms> <@user>
    elif message.content.startswith(";chui "):
        if chui_task and not chui_task.done():
            await message.channel.send("⚠️ Đang chạy `chui` rồi. Dùng `;stopchui` để dừng.")
            await message.delete()
            return

        try:
            parts = message.content.split(" ")
            if len(parts) < 3 or not message.mentions:
                await message.channel.send("`;chui <delay_ms> <@người_dùng>`")
                await message.delete()
                return

            delay_ms = int(parts[1])
            target = message.mentions[0]

            with open("text.txt", "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            if not lines:
                await message.channel.send("❌ `text.txt` không có nội dung.")
                await message.delete()
                return


            await message.delete()

            async def chui_loop():
                idx = 0
                while True:
                    content = f"{lines[idx]} {target.mention}"
                    await message.channel.send(content)
                    idx = (idx + 1) % len(lines)
                    await asyncio.sleep(delay_ms / 1000)

            chui_task = asyncio.create_task(chui_loop())

        except Exception as e:
            await message.channel.send(f"❌ Lỗi: {e}")
            await message.delete()

    # ;delwh <server_id>
    if message.content.startswith(";delwh "):
        try:
            args = message.content.split(" ")
            if len(args) != 2:
                await message.channel.send("❌ Cú pháp: `;delwh <server_id>`")
                return

            guild_id = int(args[1])
            guild = client.get_guild(guild_id)
            if not guild:
                await message.channel.send("⚠️ Không tìm thấy server.")
                return

            count = 0
            for ch in guild.text_channels:
                try:
                    webhooks = await ch.webhooks()
                    for wh in webhooks:
                        await wh.delete()
                        count += 1
                except:
                    pass

            await message.channel.send(f"🗑️ Đã xóa {count} webhook trong server `{guild.name}`.")
        except Exception as e:
            await message.channel.send(f"❌ Lỗi: {e}")

    # ;spam
    if message.content.startswith(";spam "):
        try:
            args = message.content.split(" ", 3)
            if len(args) < 4:
                await message.channel.send("❌ Cú pháp: `;spam <channel_id> <delay> <nội dung>`")
            else:
                channel_id = int(args[1])
                delay = float(args[2])
                content = args[3]

                channel = client.get_channel(channel_id)
                if not channel:
                    await message.channel.send("⚠️ Không tìm thấy kênh.")
                else:
                    if _spam_task and not _spam_task.done():
                        await message.channel.send("⚠️ Đang có spam chạy, dùng `;stopspam` để dừng.")
                    else:
                        await message.channel.send(
                            f"✅ Bắt đầu spam vào {channel.mention} với delay {delay}s. Dùng `;stopspam` để dừng."
                        )

                        async def spam_loop():
                            try:
                                while True:
                                    await channel.send(content)
                                    await asyncio.sleep(delay)
                            except asyncio.CancelledError:
                                await message.channel.send("🛑 Đã dừng spam.")
                                return

                        _spam_task = asyncio.create_task(spam_loop())
        except Exception as e:
            await message.channel.send(f"❌ Lỗi: {e}")

    # ;stopspam
    elif message.content.strip() == ";stopspam":
        if _spam_task and not _spam_task.done():
            _spam_task.cancel()
            await message.channel.send("🛑 Đã dừng spam.")
        else:
            await message.channel.send("⚠️ Không có spam nào đang chạy.")

    # Nếu có người tag mình → trả lời
    elif client.user in message.mentions and message.author.id != client.user.id:
        try:
            await message.channel.send("TAG CCASICC3M NHÀ MÀY À?")
        except Exception as e:
            print(f"Lỗi khi rep mention: {e}")


    # ;help
    elif message.content.strip() == ";help":
        await message.channel.send("""
📌 **2077 dz vl**
• `;ping`
• `;spam <chanel id> <delay> <nội_dung>` 
• `;stopspam` 
• `;ar<@user><emoji>`•`;ur`•`;av`
• `;chui<delay><@user>`•`;stopchui`

""")
        await message.delete()


client.run(TOKEN)
