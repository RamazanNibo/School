import asyncio
import os
import sqlite3
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Укажите BOT_TOKEN в файле .env")

bot = Bot(token=TOKEN)
dp = Dispatcher()
data = sqlite3.connect("school.db")
cur = data.cursor()


# Start the bot
# 启动机器人
async def main():
    create_tables()
    print("Бот работает!")
    await dp.start_polling(bot)


# Create database tables
# 创建数据库表
def create_tables():
    data.execute("""create table if not exists school (
        id integer primary key autoincrement,
        name text,
        role text,
        user_id int unique
    )""")
    data.execute("""create table if not exists lessons (
        id integer primary key autoincrement,
        name text,
        link text,
        max_points integer,
        teacher_id int
    )""")
    data.execute("""create table if not exists answers (
        id integer primary key autoincrement,
        lesson_id int,
        user_id int,
        answer text,
        points integer,
        unique(lesson_id, user_id)
    )""")

    cur.execute("pragma table_info(lessons)")
    columns = [i[1] for i in cur.fetchall()]
    if "teacher_id" not in columns:
        data.execute("alter table lessons add column teacher_id int")

    data.commit()


# Send long messages in parts
# 分段发送长消息
async def send_long(message: Message, text: str):
    for i in range(0, len(text), 4000):
        await message.answer(text[i:i + 4000])


# Get user information
# 获取用户信息
def get_user(user_id):
    cur.execute("select name,role from school where user_id = ?", (user_id,))
    return cur.fetchone()


# Check if the user is a teacher
# 检查用户是否是教师
def check_teacher(user_id):
    result = get_user(user_id)
    return result is not None and result[1] == "teacher"


# Check if the user is a student
# 检查用户是否是学生
def check_student(user_id):
    result = get_user(user_id)
    return result is not None and result[1] == "student"


# Check the entered number
# 检查输入的数字
def check_number(text):
    try:
        number = int(text)
        if number > 0:
            return number
    except (ValueError, TypeError):
        pass
    return None


# States for adding a lesson
# 添加课程时使用的状态
class AddLesson(StatesGroup):
    name = State()
    link = State()
    points = State()


# States for sending an answer
# 提交答案时使用的状态
class SolveLesson(StatesGroup):
    id = State()
    answer = State()


# States for grading an answer
# 给答案评分时使用的状态
class GradeLesson(StatesGroup):
    answer_id = State()
    points = State()


# Cancel the current action
# 取消当前操作
@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Состояние сброшено")


# Show the main menu
# 显示主菜单
@dp.message(Command("start"))
async def cmd_start(message: Message):
    create_tables()
    result = get_user(message.from_user.id)
    text = "Добро пожаловать в школу!\n\n"
    if result is None:
        text += ("Сначала зарегистрируйтесь:\n"
                 "/teacher Имя — я учитель\n"
                 "/student Имя — я ученик")
    elif result[1] == "teacher":
        text += (f"Вы учитель: {result[0]}\n\n"
                 "/add — добавить урок\n"
                 "/list — список уроков\n"
                 "/answers — ответы учеников\n"
                 "/grade — выставить оценку\n"
                 "/student Имя — стать учеником")
    else:
        text += (f"Вы ученик: {result[0]}\n\n"
                 "/list — список уроков\n"
                 "/solve — отправить ответ\n"
                 "/teacher Имя — стать учителем")
    text += "\n/cancel — отменить текущую операцию"
    await message.answer(text)


# Start adding a lesson
# 开始添加课程
@dp.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not check_teacher(user_id):
        await message.answer("Эта команда только для учителей. Стать учителем: /teacher Имя")
        return
    await message.answer("Введите название урока")
    await state.set_state(AddLesson.name)


# Save the lesson name
# 保存课程名称
@dp.message(AddLesson.name)
async def add_name(message: Message, state: FSMContext):
    if message.text is None or message.text.startswith("/") or not message.text.strip():
        await message.answer("Отправьте название текстом")
        return
    await state.update_data(name=message.text.strip())
    await message.answer("Введите ссылку")
    await state.set_state(AddLesson.link)


# Save the lesson link
# 保存课程链接
@dp.message(AddLesson.link)
async def add_link(message: Message, state: FSMContext):
    if message.text is None or message.text.startswith("/") or not message.text.strip():
        await message.answer("Отправьте ссылку текстом")
        return
    link = message.text.strip()
    if not link.startswith(("http://", "https://")):
        await message.answer("Ссылка должна начинаться с http:// или https://")
        return
    await state.update_data(link=link)
    await message.answer("Введите максимальное количество баллов")
    await state.set_state(AddLesson.points)


# Save the maximum points and add the lesson
# 保存最高分数并添加课程
@dp.message(AddLesson.points)
async def add_points(message: Message, state: FSMContext):
    points = check_number(message.text)
    if points is None:
        await message.answer("Количество баллов должно быть целым числом больше нуля")
        return
    await state.update_data(points=points)
    lesson = await state.get_data()
    data.execute("""insert into lessons (name,link,max_points,teacher_id)
                    values (?,?,?,?)""",
                 (lesson["name"], lesson["link"], lesson["points"], message.from_user.id))
    data.commit()
    await state.clear()
    await message.answer(f"Урок добавлен: {lesson['name']} (максимум {lesson['points']} баллов)")


# Show the lesson list
# 显示课程列表
@dp.message(Command("list"))
async def cmd_list(message: Message):
    user_id = message.from_user.id
    cur.execute("""select l.id, l.name, l.link, l.max_points, a.answer, a.points
                   from lessons l
                   left join answers a on a.lesson_id = l.id and a.user_id = ?
                   order by l.id""", (user_id,))
    lessons = cur.fetchall()
    if not lessons:
        await message.answer("Уроков пока нет.")
        return
    text = ""
    for lesson_id, name, link, max_points, answer, points in lessons:
        if answer is None:
            status = "ответа нет"
        elif points is None:
            status = "не оценено"
        else:
            status = f"{points} из {max_points} баллов"
        text += f"Урок {lesson_id}. {name} — {status}\n"
        text += f"{link}\n\n"
    await send_long(message, text)


# Start sending an answer
# 开始提交答案
@dp.message(Command("solve"))
async def cmd_solve(message: Message, state: FSMContext):
    if not check_student(message.from_user.id):
        await message.answer("Эта команда только для учеников. Зарегистрируйтесь: /student Имя")
        return
    await message.answer("Введите id урока (список уроков: /list)")
    await state.set_state(SolveLesson.id)


# Check the lesson ID
# 检查课程编号
@dp.message(SolveLesson.id)
async def solve_id(message: Message, state: FSMContext):
    try:
        lesson_id = int(message.text)
        if lesson_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer("Id урока должен быть положительным числом")
        return
    cur.execute("select name from lessons where id = ?", (lesson_id,))
    lesson = cur.fetchone()
    if lesson is None:
        await message.answer("Урока с таким id нет. Список уроков: /list")
        return
    await state.update_data(id=lesson_id)
    await message.answer(f"Урок: {lesson[0]}\nВведите ответ")
    await state.set_state(SolveLesson.answer)


# Save the student's answer
# 保存学生的答案
@dp.message(SolveLesson.answer)
async def solve_answer(message: Message, state: FSMContext):
    if message.text is None or message.text.startswith("/") or not message.text.strip():
        await message.answer("Отправьте ответ текстом")
        return
    if len(message.text) > 4000:
        await message.answer("Ответ слишком длинный. Максимум 4000 символов.")
        return
    lesson = await state.get_data()
    user_id = message.from_user.id
    cur.execute("select id from answers where lesson_id = ? and user_id = ?",
                (lesson["id"], user_id))
    x = cur.fetchone()
    if x is None:
        data.execute("insert into answers (lesson_id, user_id, answer) values (?,?,?)",
                     (lesson["id"], user_id, message.text.strip()))
    else:
        data.execute("update answers set answer = ?, points = null where id = ?",
                     (message.text.strip(), x[0]))
    data.commit()
    await state.clear()
    await message.answer(f"Ответ отправлен на урок {lesson['id']}")


# Register as a teacher
# 注册为教师
@dp.message(Command("teacher"))
async def cmd_teacher(message: Message):
    name = message.text.removeprefix("/teacher").strip()
    user = message.from_user.id
    result = get_user(user)

    if result is None:
        if name == "":
            await message.answer("Укажите имя: /teacher Имя")
            return
        data.execute("insert into school (name,role,user_id) values (?,?,?)",
                     (name, "teacher", user))
        data.commit()
        await message.answer(f"Вы зарегистрированы как учитель: {name}\nСписок команд: /start")
        return

    if name == "":
        name = result[0]
    if result[1] == "teacher" and name == result[0]:
        await message.answer("Вы уже зарегистрированы как учитель")
        return
    data.execute("update school set name = ?, role = ? where user_id = ?",
                 (name, "teacher", user))
    data.commit()
    if result[1] == "teacher":
        await message.answer(f"Имя изменено: {name}")
    else:
        await message.answer(f"Роль изменена на учителя. Имя: {name}\nСписок команд: /start")


# Register as a student
# 注册为学生
@dp.message(Command("student"))
async def cmd_student(message: Message):
    name = message.text.removeprefix("/student").strip()
    user = message.from_user.id
    result = get_user(user)
    if result is None:
        if name == "":
            await message.answer("Укажите имя: /student Имя")
            return
        data.execute("insert into school (name,role,user_id) values (?,?,?)",
                     (name, "student", user))
        data.commit()
        await message.answer(f"Вы зарегистрированы как ученик: {name}\nСписок команд: /start")
        return
    if name == "":
        name = result[0]
    if result[1] == "student" and name == result[0]:
        await message.answer("Вы уже зарегистрированы как ученик")
        return
    data.execute("update school set name = ?, role = ? where user_id = ?",
                 (name, "student", user))
    data.commit()
    if result[1] == "student":
        await message.answer(f"Имя изменено: {name}")
    else:
        await message.answer(f"Роль изменена на ученика. Имя: {name}\nСписок команд: /start")


# Show students' answers
# 显示学生提交的答案
@dp.message(Command("answers"))
async def cmd_answers(message: Message):
    user_id = message.from_user.id
    if not check_teacher(user_id):
        await message.answer("Эта команда только для учителей.")
        return
    cur.execute("""select a.id, l.id, l.name, s.name, a.answer, l.max_points, a.points
                   from answers a
                   join lessons l on l.id = a.lesson_id
                   left join school s on s.user_id = a.user_id
                   where l.teacher_id = ? or l.teacher_id is null
                   order by l.id, a.id""", (user_id,))
    answers = cur.fetchall()
    if not answers:
        await message.answer("Ответов пока нет.")
        return
    text = ""
    lesson = None
    for answer_id, lesson_id, name, student, answer, max_points, points in answers:
        if lesson != lesson_id:
            text += f"\nУрок {lesson_id}: {name}\n"
            lesson = lesson_id
        text += (f"\n#{answer_id} {student if student is not None else 'Без имени'}\n"
                 f"Ответ: {answer}\n"
                 f"Баллы: {points if points is not None else 'не оценено'}/{max_points}\n")
    await send_long(message, text)


# Start grading an answer
# 开始给答案评分
@dp.message(Command("grade"))
async def cmd_grade(message: Message, state: FSMContext):
    if not check_teacher(message.from_user.id):
        await message.answer("Эта команда только для учителей.")
        return
    await message.answer("Введите номер ответа (число после # в /answers)")
    await state.set_state(GradeLesson.answer_id)


# Check the answer ID
# 检查答案编号
@dp.message(GradeLesson.answer_id)
async def grade_answer_id(message: Message, state: FSMContext):
    try:
        answer_id = int(message.text)
        if answer_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer("Номер ответа должен быть положительным числом")
        return
    cur.execute("""select l.max_points, s.name
                   from answers a
                   join lessons l on l.id = a.lesson_id
                   left join school s on s.user_id = a.user_id
                   where a.id = ? and (l.teacher_id = ? or l.teacher_id is null)""",
                (answer_id, message.from_user.id))
    answer = cur.fetchone()
    if answer is None:
        await message.answer("Ответа с таким номером нет или у вас нет прав его оценивать. Список ответов: /answers")
        return
    await state.update_data(answer_id=answer_id)
    await message.answer(f"Ученик: {answer[1] if answer[1] is not None else 'Без имени'}\n"
                         f"Введите количество баллов (от 0 до {answer[0]})")
    await state.set_state(GradeLesson.points)


# Save the grade
# 保存评分
@dp.message(GradeLesson.points)
async def grade_points(message: Message, state: FSMContext):
    try:
        points = int(message.text)
    except (ValueError, TypeError):
        await message.answer("Количество баллов должно быть числом")
        return
    answer = await state.get_data()
    cur.execute("""select l.max_points
                   from answers a
                   join lessons l on l.id = a.lesson_id
                   where a.id = ? and (l.teacher_id = ? or l.teacher_id is null)""",
                (answer["answer_id"], message.from_user.id))
    x = cur.fetchone()
    if x is None:
        await message.answer("Ответ не найден или у вас нет прав его оценивать")
        await state.clear()
        return
    max_points = x[0]
    if points < 0 or points > max_points:
        await message.answer(f"Баллы должны быть от 0 до {max_points}")
        return
    data.execute("update answers set points = ? where id = ?",
                 (points, answer["answer_id"]))
    data.commit()
    await state.clear()
    await message.answer(f"Оценка выставлена: {points} из {max_points}")


asyncio.run(main())
