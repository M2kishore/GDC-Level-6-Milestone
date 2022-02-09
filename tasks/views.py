from dataclasses import field
from re import template

from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.contrib.auth.views import LoginView

from django.contrib.auth.mixins import LoginRequiredMixin

from tasks.models import Task


class AuthorizedTaskManager(LoginRequiredMixin):
    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)


class UserLoginView(LoginView):
    template_name = "user_login.html"

    # def __init__(self, *args, **kwargs):
    # super().__init__(*args, **kwargs)
    # self.fields["username"].widget.attrs["class"] = ""


class UserCreateView(CreateView):
    form_class = UserCreationForm
    template_name = "user_create.html"
    success_url = "/user/login"


def session_storage_view(request):
    total_views = request.session.get("total_views", 0)
    request.session["total_views"] = total_views + 1
    return HttpResponse(f"Total views is {total_views} and user is {request.user}")


# can inherit from class or create function to override
class GenericTaskDeleteView(AuthorizedTaskManager, DeleteView):
    model = Task
    template_name = "task_delete.html"
    success_url = "/tasks/"


class GenericTaskDetailView(DetailView):
    model = Task
    template_name = "task_detail.html"

    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)


class TaskCreateForm(ModelForm):
    def clean_title(self):
        title = self.cleaned_data["title"]
        print(title)
        if len(title) < 5:
            raise ValidationError("The data is too small")
        return title

    def clean_priority(self):
        priority = self.cleaned_data["priority"]
        if priority <= 0:
            raise ValidationError("Invalid Priority")
        return priority

    class Meta:
        model = Task
        fields = ("title", "priority", "description", "completed")


class GenericTaskUpdateView(UpdateView):
    model = Task
    form_class = TaskCreateForm
    template_name = "task_update.html"
    success_url = "/tasks"

    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)


class GenericTaskCreateView(CreateView):
    form_class = TaskCreateForm
    template_name = "task_create.html"
    success_url = "/tasks"

    def form_valid(self, form):
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class GenericTaskView(LoginRequiredMixin, ListView):
    queryset = Task.objects.filter(deleted=False)
    template_name = "tasks.html"
    context_object_name = "tasks"
    paginate_by = 5

    def get_queryset(self):
        print(self.request.user)
        tasks = Task.objects.filter(deleted=False, user=self.request.user)
        search_string = self.request.GET.get("search")
        if search_string:
            tasks = tasks.filter(title__icontains=search_string)
        return tasks


class CreateTaskView(View):
    def get(self, request):
        return render(request, "task_create.html")

    def post(self, request):
        task_string = request.POST.get("task")
        task_obj = Task(title=task_string)
        task_obj.save()
        return HttpResponseRedirect("/tasks")


class TaskView(View):
    def get(self, request):
        tasks = Task.objects.filter(deleted=False)
        search_string = request.GET.get("search")
        if search_string:
            tasks = tasks.filter(title__icontains=search_string)
        return render(request, "tasks.html", {"tasks": tasks})