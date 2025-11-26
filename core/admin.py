from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Meeting, TimeSlot, Availability

# Configura o Admin para mostrar o campo 'role' (Aluno/Professor)
class CustomUserAdmin(UserAdmin):
    # Adiciona o campo 'role' na tela de edição do usuário
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Extras', {'fields': ('role',)}),
    )
    # Adiciona o campo 'role' na tela de criação de usuário
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Extras', {'fields': ('role',)}),
    )

# Registra os modelos para aparecerem no painel
admin.site.register(User, CustomUserAdmin)
admin.site.register(Meeting)
admin.site.register(TimeSlot)
# admin.site.register(Availability) # Opcional, se quiser ver os votos