# School Telegram Bot

## English

A Telegram bot for managing school lessons and checking student answers. The bot is built with Python, aiogram 3 and SQLite. Teachers can add lessons, view students' answers and give grades. Students can view the lesson list and submit their answers.

### Features

- User registration as a teacher or a student
- Lesson list with a title, link and maximum number of points
- Teachers can add lessons
- Students can submit answers to lessons
- Students can submit an answer again; the previous answer is replaced
- Teachers can view answers submitted by students
- Teachers can grade answers from 0 up to the lesson's maximum number of points
- Students can view the status of their answers: no answer, not graded or graded
- Step-by-step dialogs built on FSM (finite state machine)
- `/cancel` command to cancel the current action
- Data stored in SQLite

### Requirements

- Python 3.10+
- aiogram 3.x
- python-dotenv
- SQLite (built into Python)

### Installation and launch

Install the dependencies:

```bash
pip install aiogram python-dotenv
```

Create a bot with [@BotFather](https://t.me/BotFather) and copy its token.

Create a `.env` file next to `school_bot.py`:

```env
BOT_TOKEN=your_telegram_bot_token
```

Run the bot:

```bash
python school_bot.py
```

On startup, the bot checks whether the required tables exist and creates them if necessary. The `school.db` database file is created automatically.

### First launch

1. Start the bot.
2. Send `/start`.
3. Register as a teacher or a student:
   - `/teacher Name`
   - `/student Name`
4. After registration, the bot shows the commands available for your role.

A user can switch roles by using the other registration command. If no name is provided, the current Telegram name is used.

### Commands

| Command | Description | Access |
|---|---|---|
| `/start` | Shows the welcome message and commands for your role | Everyone |
| `/teacher Name` | Register or switch to the teacher role | Everyone |
| `/student Name` | Register or switch to the student role | Everyone |
| `/list` | Show all lessons and your status for each one | Everyone |
| `/add` | Add a lesson: title, link and maximum points | Teacher |
| `/solve` | Submit an answer to a lesson | Student |
| `/answers` | View answers to your lessons | Teacher |
| `/grade` | Give points for a student's answer | Teacher |
| `/cancel` | Cancel the current action | Everyone |

### How it works

#### Teacher

1. Register with `/teacher Name`.
2. Create a lesson with `/add`.
3. Enter the lesson title, link and maximum number of points.
4. View students' submissions with `/answers`.
5. Grade an answer with `/grade`, entering the answer ID shown in the list.

A teacher can view and grade answers for their own lessons. Lessons created before the `teacher_id` field was added are also supported.

#### Student

1. Register with `/student Name`.
2. Open `/list` to view the available lessons.
3. Submit an answer with `/solve`, entering the lesson ID.
4. Submit the answer again if needed. The previous text is replaced and the grade is reset.
5. Use `/list` to check the status of each answer.

### Input validation

- The lesson title must not be empty.
- The link must start with `http://` or `https://`.
- The maximum number of points must be a positive integer.
- Lesson IDs and answer IDs must be positive numbers.
- A student's answer must not be empty and must not exceed 4000 characters.
- A grade must be between 0 and the lesson's maximum number of points.
- A teacher cannot grade answers to lessons created by another teacher.

### FSM (step-by-step dialogs)

The bot uses state groups for multi-step input:

| State group | Steps | Command |
|---|---|---|
| `AddLesson` | name → link → points | `/add` |
| `SolveLesson` | id → answer | `/solve` |
| `GradeLesson` | answer_id → points | `/grade` |

At each step, the bot saves the entered data with `state.update_data(...)` and moves to the next state with `state.set_state(...)`. The `/cancel` command clears the current state.

### Database

The bot uses the SQLite database file `school.db`. It contains three tables:

| Table | Columns | Purpose |
|---|---|---|
| `school` | `id`, `name`, `role`, `user_id` | Users and their roles |
| `lessons` | `id`, `name`, `link`, `max_points`, `teacher_id` | Lessons, links and maximum points |
| `answers` | `id`, `lesson_id`, `user_id`, `answer`, `points` | Student answers and grades |

Only one answer is stored for each lesson-student pair. When a student submits another answer, the existing answer is updated and its previous grade is reset.

### Project structure

```text
school-bot/
├── school_bot.py   # bot, FSM states and command handlers
├── school.db       # database, created automatically
├── .env            # Telegram bot token
└── README.md       # project description
```

### Notes

- The bot interface is in Russian.
- Grades are stored in the database. There is no online gradebook or grade export.
- The bot does not check answers automatically. Teachers review answers and give points manually.
- The `/teacher` command is available to every user. There is no secret code or separate approval for teacher registration.
- Do not publish the `.env` file or share your bot token.

---

## 中文

这是一个用于管理学校课程和检查学生答案的 Telegram 机器人。机器人使用 Python、aiogram 3 和 SQLite 编写。教师可以添加课程、查看学生提交的答案并评分。学生可以查看课程列表并提交答案。

### 功能

- 用户可以注册为教师或学生
- 课程列表包含课程名称、链接和最高分数
- 教师可以添加课程
- 学生可以提交课程答案
- 学生可以重新提交答案；新答案会替换旧答案
- 教师可以查看学生提交的答案
- 教师可以在 0 分到课程最高分之间评分
- 学生可以查看答案状态：未提交、未评分或已评分
- 使用 FSM（有限状态机）实现分步骤对话
- 使用 `/cancel` 命令取消当前操作
- 使用 SQLite 保存数据

### 环境要求

- Python 3.10+
- aiogram 3.x
- python-dotenv
- SQLite（Python 内置）

### 安装与运行

安装依赖：

```bash
pip install aiogram python-dotenv
```

通过 [@BotFather](https://t.me/BotFather) 创建机器人并复制它的 token。

在 `school_bot.py` 旁边创建 `.env` 文件：

```env
BOT_TOKEN=your_telegram_bot_token
```

运行机器人：

```bash
python school_bot.py
```

启动时，机器人会检查所需的数据表是否存在；如果不存在，就会自动创建。`school.db` 数据库文件也会自动创建。

### 首次启动

1. 启动机器人。
2. 发送 `/start`。
3. 注册为教师或学生：
   - `/teacher Name`
   - `/student Name`
4. 注册后，机器人会显示当前角色可以使用的命令。

用户可以通过另一条注册命令切换角色。如果没有输入姓名，机器人会使用当前 Telegram 名称。

### 命令

| 命令 | 说明 | 权限 |
|---|---|---|
| `/start` | 显示欢迎信息和当前角色可用的命令 | 所有人 |
| `/teacher Name` | 注册或切换为教师 | 所有人 |
| `/student Name` | 注册或切换为学生 | 所有人 |
| `/list` | 显示所有课程以及自己的答案状态 | 所有人 |
| `/add` | 添加课程：名称、链接和最高分数 | 教师 |
| `/solve` | 提交课程答案 | 学生 |
| `/answers` | 查看自己课程的学生答案 | 教师 |
| `/grade` | 为学生答案评分 | 教师 |
| `/cancel` | 取消当前操作 | 所有人 |

### 工作原理

#### 教师

1. 使用 `/teacher Name` 注册。
2. 使用 `/add` 创建课程。
3. 输入课程名称、链接和最高分数。
4. 使用 `/answers` 查看学生提交的答案。
5. 使用 `/grade` 评分，并输入列表中显示的答案 ID。

教师只能查看和评价自己课程的答案。机器人也兼容添加 `teacher_id` 字段之前创建的旧课程。

#### 学生

1. 使用 `/student Name` 注册。
2. 使用 `/list` 查看课程。
3. 使用 `/solve` 提交答案，并输入课程 ID。
4. 必要时可以重新提交答案。新文本会替换旧文本，之前的分数会被清空。
5. 使用 `/list` 查看每个答案的状态。

### 输入检查

- 课程名称不能为空。
- 链接必须以 `http://` 或 `https://` 开头。
- 最高分数必须是大于零的整数。
- 课程 ID 和答案 ID 必须是正数。
- 学生答案不能为空，且长度不能超过 4000 个字符。
- 评分必须在 0 分和课程最高分之间。
- 教师不能评价其他教师创建的课程答案。

### FSM（分步骤对话）

机器人使用状态组处理多步骤输入：

| 状态组 | 步骤 | 命令 |
|---|---|---|
| `AddLesson` | name → link → points | `/add` |
| `SolveLesson` | id → answer | `/solve` |
| `GradeLesson` | answer_id → points | `/grade` |

每一步机器人都会通过 `state.update_data(...)` 保存输入的数据，并通过 `state.set_state(...)` 进入下一步。`/cancel` 命令会清除当前状态。

### 数据库

机器人使用 SQLite 数据库文件 `school.db`，其中包含三张表：

| 表 | 字段 | 用途 |
|---|---|---|
| `school` | `id`、`name`、`role`、`user_id` | 用户及其角色 |
| `lessons` | `id`、`name`、`link`、`max_points`、`teacher_id` | 课程、链接和最高分数 |
| `answers` | `id`、`lesson_id`、`user_id`、`answer`、`points` | 学生答案和分数 |

每个“课程—学生”组合只保存一条答案。学生再次提交时，已有答案会被更新，之前的分数会被清空。

### 项目结构

```text
school-bot/
├── school_bot.py   # 机器人、FSM 状态和命令处理函数
├── school.db       # 数据库，自动创建
├── .env            # Telegram 机器人 token
└── README.md       # 项目说明
```

### 说明

- 机器人的界面语言是俄语。
- 分数保存在数据库中；没有在线成绩册或成绩导出功能。
- 机器人不会自动判断答案是否正确，教师需要手动查看答案并评分。
- 所有用户都可以使用 `/teacher` 命令注册为教师。注册教师不需要秘密代码或额外批准。
- 不要公开 `.env` 文件，也不要将机器人 token 分享给其他人。
