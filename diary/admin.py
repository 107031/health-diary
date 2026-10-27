from django.contrib import admin

from .models import ActivityType, DailyEntry, Goal, Profile, Workout

class WorkoutInline(admin.TabularInline):
    model = Workout
    extra = 0

@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'sleep_hours', 'weight_kg', 'calories', 'water_ml', 'mood')
    list_filter = ('user',)
    inlines = [WorkoutInline]

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'metric', 'target_value', 'deadline', 'is_active')


@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'kcal_per_hour')

admin.site.register(Profile)