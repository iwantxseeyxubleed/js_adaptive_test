from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    text = models.TextField(verbose_name="Текст вопроса")
    code_snippet = models.TextField(blank=True, null=True, verbose_name="Код/Листинг")
    option_a = models.CharField(max_length=255, verbose_name="Вариант А")
    option_b = models.CharField(max_length=255, verbose_name="Вариант Б")
    option_c = models.CharField(max_length=255, verbose_name="Вариант С")
    
    option_d = models.CharField(
        max_length=255, 
        default="Затрудняюсь ответить / Не знаю", 
        verbose_name="Вариант D"
    )
    
    correct_option = models.CharField(
        max_length=1, 
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], 
        verbose_name="Правильный ответ"
    )
    difficulty = models.IntegerField(verbose_name="Сложность (1-25)")
    topic = models.CharField(max_length=255, blank=True, null=True, verbose_name="Тема вопроса")
    explanation = models.TextField(blank=True, null=True, verbose_name="Пояснение")

    def __str__(self):
        return f"[{self.difficulty}] {self.text[:50]}"

class TestSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions", verbose_name="Пользователь")
    score = models.IntegerField(verbose_name="Правильных ответов")
    final_level = models.IntegerField(verbose_name="Финальный уровень сложности")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата прохождения")
    is_ai_generated = models.BooleanField(default=False, verbose_name="Тест сгенерирован ИИ")

    def __str__(self):
        return f"Сессия {self.id} — {self.user.username} ({self.date.strftime('%d.%m.%Y %H:%M')})"

class UserAnswer(models.Model):
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name="answers", verbose_name="Сессия тестирования")
    question_text = models.TextField(verbose_name="Текст вопроса на момент прохождения")
    selected_option = models.CharField(max_length=10, verbose_name="Выбранный вариант")
    status = models.CharField(max_length=20, verbose_name="Статус (correct/incorrect/dont_know)")
    difficulty_at_time = models.IntegerField(verbose_name="Сложность вопроса")

    def __str__(self):
        return f"Ответ в сессии {self.session.id} (Сложность: {self.difficulty_at_time}, Статус: {self.status})"
