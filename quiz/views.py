import json
import random
import uuid
import requests
import urllib3
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Question, TestSession, UserAnswer

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BootstrappedUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control', 
                'placeholder': field.label
            })
            if name == 'username':
                field.help_text = "До 150 симв: буквы, цифры и @/./+/-/_."
            elif 'password' in name:
                field.help_text = "Минимум 8 символов. Не слишком простой."

class BootstrappedAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control', 
                'placeholder': field.label
            })

def calculate_next_difficulty(history):
    if not history:
        return 12
    last = history[-1]
    last_diff = last['difficulty']
    status = last['status']

    if status == 'correct':
        return min(25, last_diff + 3)
    elif status == 'dont_know':
        return max(1, last_diff - 1)
    else:
        return max(1, last_diff - 4)

def get_fallback_mock_question(difficulty_level):
    ai_topics = ["Closures", "Event Loop", "Promises", "Prototypes"]
    selected_topic = random.choice(ai_topics)
    return Question(
        text=f"[Резерв ИИ] Тест концепции: {selected_topic} ({difficulty_level}/25)",
        code_snippet="const f = () => {\n  let x = 0;\n  return () => ++x;\n};",
        option_a="1", option_b="0", option_c="undefined",
        correct_option="A",
        difficulty=difficulty_level,
        topic=selected_topic,
        explanation="Локальный фолбек: сбой сети при обращении к GigaChat API, активирован резервный пул."
    )

def generate_question_via_ai(difficulty_level):
    GIGACHAT_AUTH = "MDE5ZWE4ZmItNzY5ZS03YmEyLThiMTktOThiYjFkOWQzODkyOjQzZDUyMjE4LWE3YjgtNDFkMy05MzY3LWY5MmU0ZGNiNDdlZA=="
    
    oauth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    rquid = str(uuid.uuid4())
    
    oauth_headers = {
        "Authorization": f"Basic {GIGACHAT_AUTH}",
        "RqUID": rquid,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    oauth_data = {"scope": "GIGACHAT_API_PERS"}
    
    try:
        token_res = requests.post(
            oauth_url, headers=oauth_headers, data=oauth_data, verify=False, timeout=5
        )
        if token_res.status_code != 200:
            return get_fallback_mock_question(difficulty_level)
            
        access_token = token_res.json().get("access_token")
        
        api_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        prompt = (
            f"Ты — генератор адаптивных тестов по JavaScript. Сгенерируй один вопрос.\n"
            f"Сложность: {difficulty_level} из 25.\n"
            f"Ответ должен быть строго валидным JSON со следующей структурой:\n"
            f"{{\n"
            f"  \"text\": \"Текст вопроса по JS\",\n"
            f"  \"code_snippet\": \"Код с переносами строк \\n или null\",\n"
            f"  \"option_a\": \"Вариант А\",\n"
            f"  \"option_b\": \"Вариант Б\",\n"
            f"  \"option_c\": \"Вариант В\",\n"
            f"  \"correct_option\": \"A\" или \"B\" или \"C\",\n"
            f"  \"topic\": \"Название темы\",\n"
            f"  \"explanation\": \"Пояснение\"\n"
            f"}}"
        )
        
        payload = {
            "model": "GigaChat",
            "messages": [
                {"role": "system", "content": "Ты строгий генератор JSON. Возвращай только чистый JSON без разметки markdown."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        res = requests.post(api_url, json=payload, headers=headers, verify=False, timeout=8)
        if res.status_code == 200:
            res_data = res.json()
            raw_text = res_data['choices'][0]['message']['content'].strip()
            
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            parsed = json.loads(raw_text.strip())
            
            return Question(
                text=parsed.get("text", "Вопрос по JS"),
                code_snippet=parsed.get("code_snippet"),
                option_a=parsed.get("option_a", "Вариант А"),
                option_b=parsed.get("option_b", "Вариант Б"),
                option_c=parsed.get("option_c", "Вариант В"),
                correct_option=parsed.get("correct_option", "A"),
                difficulty=difficulty_level,
                topic=parsed.get("topic", "Общий раздел JS"),
                explanation=parsed.get("explanation", "Разбор темы выполнен GigaChat API.")
            )
    except Exception as e:
        print(f"--> [Error]: {e}")
        
    return get_fallback_mock_question(difficulty_level)

def register_view(request):
    if request.method == 'POST':
        form = BootstrappedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('welcome')
    else:
        form = BootstrappedUserCreationForm()
    return render(request, 'quiz/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = BootstrappedAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('welcome')
    else:
        form = BootstrappedAuthenticationForm()
    return render(request, 'quiz/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def welcome_view(request):
    if 'use_ai' not in request.session:
        request.session['use_ai'] = False
    return render(request, 'quiz/welcome.html')

@login_required
def toggle_ai_view(request):
    request.session['use_ai'] = not request.session.get('use_ai', False)
    return redirect('welcome')

@login_required
def start_view(request):
    request.session['current_question_idx'] = 0
    request.session['score'] = 0
    request.session['quiz_history'] = []  
    request.session['asked_ids'] = []     
    request.session['current_difficulty'] = 12 
    request.session['current_session_saved'] = False  
    return redirect('question')

@login_required
def question_view(request):
    current_idx = request.session.get('current_question_idx', 0)
    if current_idx >= 5:
        return redirect('result')
        
    target_difficulty = request.session.get('current_difficulty', 12)
    use_ai = request.session.get('use_ai', False)

    if use_ai:
        question = generate_question_via_ai(target_difficulty)
        request.session['ai_question_data'] = {
            'text': question.text,
            'code_snippet': question.code_snippet,
            'option_a': question.option_a,
            'option_b': question.option_b,
            'option_c': question.option_c,
            'correct_option': question.correct_option,
            'difficulty': question.difficulty,
            'topic': question.topic,
            'explanation': question.explanation
        }
    else:
        asked_ids = request.session.get('asked_ids', [])
        pool = Question.objects.filter(
            difficulty=target_difficulty
        ).exclude(id__in=asked_ids)
        
        if not pool.exists():
            pool = Question.objects.exclude(id__in=asked_ids)
            if not pool.exists():
                return redirect('result') 
            question = min(pool, key=lambda q: abs(q.difficulty - target_difficulty))
        else:
            question = random.choice(pool)

        request.session['current_question_id'] = question.id
        request.session['ai_question_data'] = None

    return render(request, 'quiz/test.html', {
        'question': question, 
        'question_num': current_idx + 1
    })

@login_required
def submit_view(request):
    if request.method == 'POST':
        current_idx = request.session.get('current_question_idx', 0)
        use_ai = request.session.get('use_ai', False)
        selected_answer = request.POST.get('answer')
        
        history = request.session.get('quiz_history', [])
        asked_ids = request.session.get('asked_ids', [])
        target_diff = request.session.get('current_difficulty', 12)

        if use_ai:
            ai_data = request.session.get('ai_question_data')
            correct_option = ai_data['correct_option']
            q_text = ai_data['text']
            q_topic = ai_data['topic']
            q_explanation = ai_data['explanation']
        else:
            question_id = request.session.get('current_question_id')
            try:
                question = Question.objects.get(id=question_id)
                correct_option = question.correct_option
                q_text = question.text
                q_topic = question.topic
                q_explanation = question.explanation
                asked_ids.append(question.id)
            except Question.DoesNotExist:
                return redirect('question')

        if selected_answer == 'dont_know':
            status = 'dont_know'
        elif selected_answer == correct_option:
            status = 'correct'
            request.session['score'] = request.session.get('score', 0) + 1
        else:
            status = 'incorrect'

        history.append({
            'text': q_text,
            'topic': q_topic,
            'explanation': q_explanation,
            'difficulty': target_diff, 
            'status': status,
            'selected': selected_answer
        })

        next_difficulty = calculate_next_difficulty(history)

        request.session['quiz_history'] = history
        request.session['asked_ids'] = asked_ids
        request.session['current_difficulty'] = next_difficulty
        request.session['current_question_idx'] = current_idx + 1
            
    return redirect('question')

@login_required
def result_view(request):
    score = request.session.get('score', 0)
    final_level = request.session.get('current_difficulty', 12)
    history = request.session.get('quiz_history', [])
    use_ai = request.session.get('use_ai', False)

    saved_flag = 'current_session_saved'
    is_saved = request.session.get(saved_flag, False)
    
    if history and not is_saved:
        session_obj = TestSession.objects.create(
            user=request.user,
            score=score,
            final_level=final_level,
            is_ai_generated=use_ai
        )
        for item in history:
            UserAnswer.objects.create(
                session=session_obj,
                question_text=item['text'],
                selected_option=item['selected'],
                status=item['status'],
                difficulty_at_time=item['difficulty']
            )
        request.session[saved_flag] = True

    return render(request, 'quiz/result.html', {
        'score': score, 
        'level': final_level,
        'history': history,
    })

@login_required
def profile_view(request):
    sessions = TestSession.objects.filter(user=request.user).order_by('-date')
    
    chart_dates = []
    chart_levels = []
    
    for s in reversed(sessions[:10]): 
        chart_dates.append(s.date.strftime('%d.%m %H:%M'))
        chart_levels.append(s.final_level)

    context = {
        'sessions': sessions,
        'chart_dates': chart_dates,
        'chart_levels': chart_levels,
        'total_tests': sessions.count(),
    }
    return render(request, 'quiz/profile.html', context)
