# SlackApp for Kintai

<img src="./image/3.png" width="75%">
<img src="./image/5.png" width="75%">

# Slack と Notion で勤怠・進捗管理ができるアプリ

### **メンションで出勤ボタンを表示**

<img src="./image/1.png" width="75%">
</br>

### **スレッドで出勤退勤時間を記録**

<img src="./image/4.png" width="75%">
</br>

### **勤務中はステータスを変更**

<img src="./image/6.png" width="75%">
</br>

### **Notionでまとめて管理**

<img src="./image/8.png" width="75%">
</br>
</br>

### **使用技術**

Bolt for Python (SlackAPI SDK)  
Notion API  
AWS Lambda
</br>
</br>

### **SlackApp に必要なスコープ**

**Bot Token Scopes**

- app_mentions:read
- channels:history
- chat:write
- reactions:write

**User Token Scopes**

- users.profile:write
