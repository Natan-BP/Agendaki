from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.db.models import Count
from django.db import models
import calendar
from django.urls import reverse
from datetime import date, datetime, timedelta
from .forms import SignUpForm, MeetingForm, TimeSlotForm
from .models import Meeting, TimeSlot, Availability, User
from datetime import datetime, timedelta, time
from .forms import SignUpForm, MeetingForm, TimeSlotForm, GenerateSlotsForm # <Adicione GenerateSlotsForm


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # loga o usuário assim que ele se cadastra
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'signup.html', {'form': form})



@login_required(login_url='/login/')
def home_view(request):
    user = request.user
    
    # 1. Filtros de Reuniões 
    meetings_as_leader = Meeting.objects.filter(leader=user, status=Meeting.Status.EM_VOTACAO)
    
    confirmed_meetings = Meeting.objects.filter(
        status=Meeting.Status.CONFIRMADA
    ).filter(
        models.Q(leader=user) | models.Q(availabilities__user=user)
    ).distinct().order_by('chosen_start')

    voted_meetings = Meeting.objects.filter(
        availabilities__user=user, status=Meeting.Status.EM_VOTACAO
    ).exclude(leader=user).distinct()

    # 2. Lógica do Calendário 
    today = datetime.now()
    year, month = today.year, today.month
    
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    calendar_weeks = []
    
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                # Criamos uma data completa para comparar com precisão
                current_day_date = datetime(year, month, day).date()
                today_date = today.date()

                day_events = []
                for m in confirmed_meetings:
                    if m.chosen_start.date() == current_day_date:
                        day_events.append(m)
                
                week_data.append({
                    'day': day,
                    'is_today': (current_day_date == today_date),
                    'is_past': (current_day_date < today_date),
                    'events': day_events
                })
                
        calendar_weeks.append(week_data)

    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    return render(request, 'home.html', {
        'meetings_as_leader': meetings_as_leader,
        'confirmed_meetings': confirmed_meetings,
        'voted_meetings': voted_meetings,
        'calendar_weeks': calendar_weeks,
        'current_month_name': meses[month - 1],
        'current_year': year,
    })

def is_professor(user):
    return user.is_authenticated and user.role == 'PROFESSOR'

@user_passes_test(is_professor, login_url='/login/')
def create_meeting_view(request):
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.leader = request.user  # professor logado
            meeting.save()
            return redirect('home')
    else:
        form = MeetingForm()

    return render(request, 'meeting_form.html', {'form': form})

@user_passes_test(is_professor, login_url='/login/')
def reopen_meeting_view(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)

    if meeting.leader != request.user:
        return HttpResponseForbidden('Você não é o líder desta reunião.')

    meeting.status = Meeting.Status.EM_VOTACAO
    meeting.chosen_start = None
    meeting.chosen_end = None
    meeting.save()

    return redirect('meeting_detail', meeting_id=meeting.id)

@login_required(login_url='/login/')
def meeting_detail_view(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)

    # slots com número de votos
    time_slots = meeting.time_slots.annotate(
        num_votos=Count('availabilities')
    ).prefetch_related('availabilities__user').order_by('start')

    # participantes = quem já marcou disponibilidade
    participants = User.objects.filter(
        availabilities__meeting=meeting
    ).distinct()

    # URL completa de convite por link
    invite_url = request.build_absolute_uri(
        reverse('meeting_invite', args=[meeting.invite_token])
    )

    return render(request, 'meeting_detail.html', {
        'meeting': meeting,
        'time_slots': time_slots,
        'participants': participants,
        'invite_url': invite_url,
    })

@login_required(login_url='/login/')
def meeting_invite_view(request, token):
    meeting = get_object_or_404(Meeting, invite_token=token)
    return redirect('meeting_detail', meeting_id=meeting.id)


@user_passes_test(lambda u: u.is_authenticated and u.role == 'PROFESSOR', login_url='/login/')
def manage_timeslots_view(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)

    if meeting.leader != request.user:
        return HttpResponseForbidden('Você não é o líder desta reunião.')

    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.meeting = meeting
            slot.save()
            return redirect('manage_timeslots', meeting_id=meeting.id)
    else:
        form = TimeSlotForm()

    generate_form = GenerateSlotsForm()

    slots = meeting.time_slots.all().order_by('start')

    meeting_form = MeetingForm(instance=meeting)

    return render(request, 'manage_timeslots.html', {
        'meeting': meeting,
        'form': form,
        'slots': slots,
        'generate_form': generate_form,
        'meeting_form': meeting_form,
    })


@login_required(login_url='/login/')
def vote_view(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    if meeting.status != Meeting.Status.EM_VOTACAO:
        # Retorna erro 403 (Proibido) ou redireciona com aviso
        return HttpResponseForbidden("Esta votação já foi encerrada e o horário definido.")

    slots = meeting.time_slots.all().order_by('start')

    # slots que o usuário já marcou antes
    user_slots_ids = set(
        Availability.objects.filter(
            meeting=meeting,
            user=request.user
        ).values_list('timeslot_id', flat=True)
    )

    if request.method == 'POST':
        selected_ids = request.POST.getlist('slots')  # lista de strings
        selected_ids = [int(s) for s in selected_ids]

        # apaga disponibilidades antigas desse usuário nessa reunião
        Availability.objects.filter(
            meeting=meeting,
            user=request.user
        ).delete()

        # cria as novas
        novas = []
        for slot_id in selected_ids:
            # garante que o slot pertence a essa meeting
            slot = slots.filter(id=slot_id).first()
            if slot:
                novas.append(Availability(
                    meeting=meeting,
                    timeslot=slot,
                    user=request.user
                ))
        Availability.objects.bulk_create(novas)

        return redirect('meeting_detail', meeting_id=meeting.id)

    return render(request, 'vote_meeting.html', {
        'meeting': meeting,
        'slots': slots,
        'user_slots_ids': user_slots_ids,
    })

@user_passes_test(lambda u: u.is_authenticated and u.role == 'PROFESSOR', login_url='/login/')
def confirm_slot_view(request, meeting_id, slot_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    if meeting.leader != request.user:
        return HttpResponseForbidden('Você não é o líder desta reunião.')

    slot = get_object_or_404(TimeSlot, id=slot_id, meeting=meeting)

    # define horário final
    meeting.chosen_start = slot.start
    meeting.chosen_end = slot.end
    meeting.status = Meeting.Status.CONFIRMADA
    meeting.save()

    return redirect('meeting_detail', meeting_id=meeting.id)

@login_required(login_url='/login/')
def calendar_view(request):
    today = date.today()
    year = today.year
    month = today.month

    # info do mês
    first_weekday, num_days = calendar.monthrange(year, month)  # Monday = 0
    all_days = [date(year, month, d) for d in range(1, num_days + 1)]

    # reuniões confirmadas do usuário
    confirmed = Meeting.objects.filter(
        status=Meeting.Status.CONFIRMADA
    ).filter(
        models.Q(leader=request.user) |
        models.Q(availabilities__user=request.user)
    ).distinct()

    # monta semanas: lista de semanas, cada semana = lista de 7 "células"
    # cada célula é None ou um dict {'date': date, 'events': [meetings]}
    weeks = []
    week = []

    # preenche espaços vazios antes do 1º dia
    for _ in range(first_weekday):
        week.append(None)

    for d in all_days:
        # eventos nesse dia
        events = [m for m in confirmed
                  if m.chosen_start and m.chosen_start.date() == d]

        week.append({
            'date': d,
            'events': events,
        })

        if len(week) == 7:
            weeks.append(week)
            week = []

    # completa a última semana com None
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)

    month_name = today.strftime("%B")  # se quiser em PT-BR dá pra trocar depois

    return render(request, 'calendar.html', {
        'year': year,
        'month': month_name,
        'weeks': weeks,
    })

@user_passes_test(lambda u: u.is_authenticated and u.role == 'PROFESSOR', login_url='/login/')
def generate_slots_view(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    if meeting.leader != request.user:
        return HttpResponseForbidden('Você não é o líder desta reunião.')

    if request.method == 'POST':
        form = GenerateSlotsForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # Combina a data com a hora para criar o datetime completo
            current_time = datetime.combine(data['date'], data['start_time'])
            end_limit = datetime.combine(data['date'], data['end_time'])
            interval = timedelta(minutes=data['interval'])
            
            # Loop para criar os horários
            slots_to_create = []
            while current_time + interval <= end_limit:
                end_slot = current_time + interval
                slots_to_create.append(TimeSlot(
                    meeting=meeting,
                    start=current_time,
                    end=end_slot
                ))
                current_time = end_slot
            
            # Salva tudo de uma vez no banco (mais rápido)
            TimeSlot.objects.bulk_create(slots_to_create)
            
    return redirect('manage_timeslots', meeting_id=meeting.id)

# --- FUNÇÃO DE DELETAR HORARIO ---
@user_passes_test(lambda u: u.is_authenticated and u.role == 'PROFESSOR', login_url='/login/')
def delete_slot_view(request, meeting_id, slot_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    slot = get_object_or_404(TimeSlot, id=slot_id, meeting=meeting)

    # Segurança: só o dono da reunião pode deletar
    if request.user != meeting.leader:
        return HttpResponseForbidden("Você não tem permissão para alterar esta reunião.")

    if request.method == 'POST':
        slot.delete()
        return redirect('manage_timeslots', meeting_id=meeting.id)
    
    # Se tentar acessar por GET (sem clicar no botão), volta para a lista
    return redirect('manage_timeslots', meeting_id=meeting.id)


# --- FUNÇÃO DE EDITAR HORARIO ---
@user_passes_test(lambda u: u.is_authenticated and u.role == 'PROFESSOR', login_url='/login/')
def edit_slot_view(request, meeting_id, slot_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    slot = get_object_or_404(TimeSlot, id=slot_id, meeting=meeting)

    if request.user != meeting.leader:
        return HttpResponseForbidden("Você não tem permissão.")

    # O segredo da edição: instance=slot (preenche o formulário com os dados atuais)
    if request.method == 'POST':
        form = TimeSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            return redirect('manage_timeslots', meeting_id=meeting.id)
    else:
        form = TimeSlotForm(instance=slot)

    # Vamos usar um template simples só para essa edição
    return render(request, 'slot_edit_form.html', {
        'form': form,
        'meeting': meeting,
        'slot': slot
    })

# --- FUNÇÕES DE EDIÇÃO E EXCLUSÃO DE AGENDAMENTO---
@user_passes_test(lambda u: u.is_authenticated and u.role == 'PROFESSOR', login_url='/login/')
def update_meeting_details(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    if request.user != meeting.leader:
        return HttpResponseForbidden("Sem permissão.")

    if request.method == 'POST':
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            # Volta para a mesma página com os dados atualizados
            return redirect('manage_timeslots', meeting_id=meeting.id)
    
    return redirect('manage_timeslots', meeting_id=meeting.id)

@user_passes_test(lambda u: u.is_authenticated and u.role == 'PROFESSOR', login_url='/login/')
def delete_meeting_view(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
    
    if request.user != meeting.leader:
        return HttpResponseForbidden("Sem permissão.")

    if request.method == 'POST':
        meeting.delete()
        # Se deletou, não tem como voltar. Vai para a Home.
        return redirect('home')
    
    return redirect('manage_timeslots', meeting_id=meeting.id)