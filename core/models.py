from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class User(AbstractUser):
    class Role(models.TextChoices):
        ALUNO = 'ALUNO', 'Aluno'
        PROFESSOR = 'PROFESSOR', 'Professor'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ALUNO,
    )
    
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)


class Meeting(models.Model):
    class Status(models.TextChoices):
        EM_VOTACAO = 'EM_VOTACAO', 'Em votação'
        CONFIRMADA = 'CONFIRMADA', 'Confirmada'
        FINALIZADA = 'FINALIZADA', 'Finalizada'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    leader = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='meetings_as_leader'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.EM_VOTACAO
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # ➕ NOVO: token único para convite por link
    invite_token = models.UUIDField(default=uuid.uuid4, unique=True)

    # horário final escolhido
    chosen_start = models.DateTimeField(null=True, blank=True)
    chosen_end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title



class TimeSlot(models.Model):
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='time_slots'
    )
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        return f'{self.meeting.title}: {self.start} - {self.end}'


class Availability(models.Model):
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )
    timeslot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )

    class Meta:
        unique_together = ('timeslot', 'user')  # 1 voto por slot

    def __str__(self):
        return f'{self.user} disponível em {self.timeslot}'
