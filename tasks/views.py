from dataclasses import field
from re import template

from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm, NullBooleanField

# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.contrib.auth.views import LoginView

from django.contrib.auth.mixins import LoginRequiredMixin

from tasks.models import Report, Task


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

    def form_valid(self, form):
        self.object = form.save()
        Report.objects.create(user=self.object)
        return HttpResponseRedirect(self.get_success_url())


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


class ReportForm(ModelForm):
    class Meta:
        model = Report
        fields = [
            "report_time",
        ]


class GenericTaskUpdateView(UpdateView):
    model = Task
    form_class = TaskCreateForm
    template_name = "task_update.html"
    success_url = "/tasks"

    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)

    def form_valid(self, form):
        self.object = form.save()
        priority = self.object.priority
        user = self.request.user
        id = self.object.id
        handle_duplicates(user, priority, id)
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class GenericTaskCreateView(LoginRequiredMixin, CreateView):
    form_class = TaskCreateForm
    template_name = "task_create.html"
    success_url = "/tasks"

    def form_valid(self, form):
        self.object = form.save()
        priority = self.object.priority
        user = self.request.user
        handle_duplicates(user, priority)
        self.object.user = user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class GenericCompletedTaskView(LoginRequiredMixin, ListView):
    template_name = "tasks.html"
    context_object_name = "tasks"

    def get_queryset(self):
        return getTasks(
            deleted=False,
            completed=True,
            user=self.request.user,
            search_string=self.request.GET.get("search"),
        )


class GenericPendingTaskView(LoginRequiredMixin, ListView):
    template_name = "tasks.html"
    context_object_name = "tasks"

    def get_queryset(self):
        return getTasks(
            deleted=False,
            completed=False,
            user=self.request.user,
            search_string=self.request.GET.get("search"),
        )


class GenericTaskView(LoginRequiredMixin, ListView):
    # queryset = Task.objects.filter(deleted=False)
    template_name = "tasks.html"
    context_object_name = "tasks"
    # paginate_by = 5

    def get_queryset(self):
        return getTasks(deleted=False, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(GenericTaskView, self).get_context_data(**kwargs)
        context.update(
            {
                "report_id": Report.objects.get(user=self.request.user).pk,
            }
        )
        return context


class GenericReportView(UpdateView):
    queryset = Report.objects.all()
    form_class = ReportForm
    success_url = "/tasks"
    template_name = "report.html"


# helper functions
def handle_duplicates(user, priority, id=-1):
    bulk_object = []
    overlap_task = Task.objects.filter(
        priority=priority, user=user, deleted=False, completed=False
    ).first()

    # if update happens and priority is not changed
    if overlap_task is not None:

        if (
            overlap_task.id == id
            and overlap_task.priority == priority
            and overlap_task.user == user
        ):
            return

    while overlap_task is not None:
        overlap_task.priority += 1
        bulk_object.append(overlap_task)
        overlap_task = Task.objects.filter(
            priority=overlap_task.priority, user=user, deleted=False, completed=False
        ).first()
    Task.objects.bulk_update(bulk_object, ["priority"])


def getTasks(deleted, user, completed=False, search_string=""):
    tasks = Task.objects.filter(
        deleted=deleted, completed=completed, user=user
    ).order_by("priority")
    if search_string:
        tasks = tasks.filter(title__icontains=search_string)
    return tasks


# class CreateTaskView(View):
#     def get(self, request):
#         return render(request, "task_create.html")

#     def post(self, request):
#         task_string = request.POST.get("task")
#         task_obj = Task(title=task_string)
#         task_obj.save()
#         return HttpResponseRedirect("/tasks")


# class TaskView(View):
#     def get(self, request):
#         tasks = Task.objects.filter(deleted=False)
#         search_string = request.GET.get("search")
#         if search_string:
#             tasks = tasks.filter(title__icontains=search_string)
#         return render(request, "tasks.html", {"tasks": tasks})