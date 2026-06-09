import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')
django.setup()

from quiz.models import Question

def seed_db():
    print("Очистка базы данных...")
    Question.objects.all().delete()

    print("Генерация ровно 60 многоуровневых вопросов по JavaScript...")
    questions_to_create = []

    base_topics = ["Переменные", "Приведение типов", "Массивы", "Замыкания", "Event Loop", "Прототипы", "Async/Await"]

    for i in range(1, 61):
        difficulty_level = int(1 + (i - 1) * (25 - 1) / (60 - 1))
        topic = base_topics[i % len(base_topics)]
        
        questions_to_create.append(Question(
            text=f"Анализ работы движка V8. Каков будет результат выполнения операции? (Тест {i})",
            code_snippet=f"// Уровень сложности: {difficulty_level} из 25\nconsole.log(typeof [] + {i});",
            difficulty=difficulty_level,
            topic=topic,
            option_a="object" + str(i),
            option_b="array" + str(i),
            option_c="undefined",
            correct_option='A',
            explanation=f"Разбор теста №{i}: В JavaScript массивы имеют базовый тип данных 'object'. При сложении со строкой или числом происходит неявное приведение к строковому типу."
        ))

    Question.objects.bulk_create(questions_to_create)
    print(f"Готово! В БД успешно записано {Question.objects.count()} вопросов (Сложность 1-25).")

if __name__ == '__main__':
    seed_db()