from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Question, Answer, Comment, Tag
from .forms import QuestionForm, AnswerForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
import json
import datetime
from django.contrib.contenttypes.models import ContentType
from django.http import *
from django.urls import reverse


# List of all questions
def question_list(request):
    tag_names = request.GET.getlist('tags')
    selected_year = request.GET.get('year')
    sort_by = request.GET.get('sort', 'date')  # Default sorting by date
    search_query = request.GET.get('search', '')  # Search query

    # Filter by tags
    if tag_names:
        questions = Question.objects.filter(tags__name__in=tag_names).distinct()
    else:
        questions = Question.objects.all()

    # Filter by year
    if selected_year:
        questions = questions.filter(created_at__year=selected_year)
    
    # Search filter
    if search_query:
        questions = questions.filter(title__icontains=search_query)

    # Sorting
    if sort_by == 'date':
        questions = questions.order_by('-created_at')  # Sort by creation date, descending
    elif sort_by == 'date_asc':
        questions = questions.order_by('created_at')  # Sort by creation date, ascending

    # Get all unique years for the dropdown
    years = Question.objects.dates('created_at', 'year').distinct()
    tags = Tag.objects.all()

    return render(request, 'questions/question_list.html', {
        'questions': questions,
        'tags': tags,
        'selected_tags': tag_names,
        'sort_by': sort_by,
        'years': years,
        'selected_year': selected_year,
        'search_query': search_query
    })

# Create a question
@login_required
def create_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.user = request.user
            question.save()
            form.save_m2m()
            return redirect('question_list')
    else:
        form = QuestionForm()
    return render(request, 'questions/create_question.html', {'form': form})

# Detail view of a question
def question_detail(request, pk):
    question = get_object_or_404(Question, pk=pk)
    answers = question.answers.all()
    comment_form = CommentForm()
    answer_form = AnswerForm()
    return render(request, 'questions/question_detail.html', {
        'question': question,
        'answers': answers,
        'comment_form': comment_form,
        'answer_form': answer_form
    })

# Edit a question
@login_required
def edit_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.user != question.user:
        return redirect('question_detail', pk=pk)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('question_detail', pk=pk)
    else:
        form = QuestionForm(instance=question)
    return render(request, 'questions/edit_question.html', {'form': form})

# Delete a question
@login_required
def delete_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.user == question.user:
        question.delete()
    return redirect('question_list')

@login_required
def edit_answer(request, question_pk,answer_pk):
    question = get_object_or_404(Question, pk=question_pk)
    answer = get_object_or_404(Answer, pk=answer_pk)
    if request.user != answer.user:
        return redirect('question_detail', pk=question_pk)
    if request.method == 'POST':
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            return redirect('question_detail', pk=question_pk)
    else:
        form = AnswerForm(instance=answer)
    return render(request, 'questions/edit_answer.html', {'form': form})

# Delete a question
@login_required
def delete_answer(request,question_pk,answer_pk):
    question = get_object_or_404(Question, pk=question_pk)
    answer = get_object_or_404(Answer, pk=answer_pk)
    if request.user == answer.user:
        answer.delete()
    return redirect('question_detail',pk=question_pk)





# Answer a question
@login_required
def create_answer(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.user = request.user
            answer.save()
            return redirect('question_detail', pk=pk)
    else:
        form = AnswerForm()
    return render(request, 'questions/create_answer.html', {'form': form, 'question': question})

# Comment on a question or answer
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Question, Answer, Comment
from .forms import CommentForm

@login_required
def create_comment(request, question_pk, answer_pk=None):
    question = get_object_or_404(Question, pk=question_pk)
    if answer_pk:
        related_object = get_object_or_404(Answer, pk=answer_pk)
    else:
        related_object = question
    
    parent_comment = None
    
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            if answer_pk:
                comment.answer = related_object
            else:
                comment.question = related_object
            comment.parent = parent_comment
            comment.save()
            return redirect('question_detail', pk=question_pk)
    else:
        form = CommentForm()
    return render(request, 'questions/create_comment.html', {
        'form': form,
        'question': question,
        'parent_comment': parent_comment
    })


@login_required
def create_comment_answer(request, question_pk, answer_pk=None, parent_pk=None):
    question = get_object_or_404(Question, pk=question_pk)
    if answer_pk:
        related_object = get_object_or_404(Answer, pk=answer_pk)
    else:
        related_object = question
    
    parent_comment = None
    if parent_pk:
        parent_comment = get_object_or_404(Comment, pk=parent_pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            if answer_pk:
                comment.answer = related_object
            else:
                comment.question = related_object
            comment.parent = parent_comment
            comment.save()
            return redirect('question_detail', pk=question_pk)
    else:
        form = CommentForm()
    return render(request, 'questions/create_comment.html', {
        'form': form,
        'question': question,
        'parent_comment': parent_comment
    })

@login_required
def like_question(request, question_pk):
    question= get_object_or_404(Question, id=question_pk)
    if question.likes.filter(id=request.user.id).exists():
        pass
    else:
        question.likes.add(request.user)
        question.unlikes.remove(request.user)
    return redirect('question_detail', pk=question_pk)

@login_required
def unlike_question(request, question_pk):
    question = get_object_or_404(Question, id=question_pk)
    if question.unlikes.filter(id=request.user.id).exists():
        # question.unlikes.remove(request.user)
        pass
    else:
        question.unlikes.add(request.user)
        question.likes.remove(request.user)
    return redirect('question_detail', pk=question_pk)


# Upvote/Downvote a question, answer, or comment

@login_required
def like_answer(request, question_pk,answer_pk):
    question= get_object_or_404(Question, id=question_pk)
    answer = get_object_or_404(Answer, id=answer_pk)
    if answer.likes.filter(id=request.user.id).exists():
        pass
    else:
        answer.likes.add(request.user)
        answer.unlikes.remove(request.user)
    return redirect('question_detail', pk=question_pk)

@login_required
def unlike_answer(request, question_pk,answer_pk):
    question = get_object_or_404(Question, id=question_pk)
    answer = get_object_or_404(Answer, id=answer_pk)
    if answer.unlikes.filter(id=request.user.id).exists():
        # question.unlikes.remove(request.user)
        pass
    else:
        answer.unlikes.add(request.user)
        answer.likes.remove(request.user)
    return redirect('question_detail', pk=question_pk)

@login_required
def like_comment(request, question_pk,answer_pk=None,comment_pk=None):
    question= get_object_or_404(Question, id=question_pk)
    if answer_pk: answer = get_object_or_404(Answer, id=answer_pk)

    comment=get_object_or_404(Comment,pk=comment_pk)

    if comment.likes.filter(id=request.user.id).exists():
        pass
    else:
        comment.likes.add(request.user)
        comment.unlikes.remove(request.user)

    if answer_pk: 
        answer = get_object_or_404(Answer, id=answer_pk)
        return redirect('question_answer_comment',question_pk,answer_pk)
    return redirect('question_detail', pk=question_pk)

@login_required
def unlike_comment(request, question_pk,answer_pk=None,comment_pk=None):
    question= get_object_or_404(Question, id=question_pk)
    if answer_pk: answer = get_object_or_404(Answer, id=answer_pk)

    comment=get_object_or_404(Comment,pk=comment_pk)
    if comment.unlikes.filter(id=request.user.id).exists():
        # question.unlikes.remove(request.user)
        pass
    else:
        comment.unlikes.add(request.user)
        comment.likes.remove(request.user)

    if answer_pk: 
        answer = get_object_or_404(Answer, id=answer_pk)
        return redirect('question_answer_comment',question_pk,answer_pk)
       
    return redirect('question_detail', pk=question_pk)


# Filter questions by tag
def filter_by_tag(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    questions = tag.question_set.all().order_by('-created_at')
    return render(request, 'questions/question_list.html', {'questions': questions, 'tag': tag})


def question_answer_comment(request,question_pk, answer_pk):
    question = get_object_or_404(Question, pk=question_pk)
    answer = get_object_or_404(Answer, pk=answer_pk)
    comments = answer.comments.all().order_by('-created_at')
    return render(request, 'questions/question_answer_comment.html', {'question': question, 'answer':
                                                                      answer, 'comments': comments})
    
@login_required
def edit_comment(request, question_pk, answer_pk=None, comment_pk=None):
    question = get_object_or_404(Question, pk=question_pk)
    comment = get_object_or_404(Comment, pk=comment_pk)
    
    if request.user != comment.user:
        return redirect('question_detail', pk=question_pk)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            if answer_pk:
                return redirect('question_answer_comment', question_pk=question_pk, answer_pk=answer_pk)

            return redirect('question_detail', pk=question_pk)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'questions/edit_comment.html', {'form': form})

# Delete a question
@login_required
def delete_comment(request, question_pk, answer_pk=None, comment_pk=None):
    question = get_object_or_404(Question, pk=question_pk)
    comment = get_object_or_404(Comment, pk=comment_pk)
    
    # Check if the user is the author of the comment
    if request.user == comment.user:
        comment.delete()
    
    # Redirect to the appropriate page based on whether the comment is on a question or an answer
    if answer_pk:
        return redirect('question_answer_comment', question_pk=question_pk, answer_pk=answer_pk)
    return redirect('question_detail', pk=question_pk)




from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/home')  # Redirect to a home page or another page after signup
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})



from django.contrib.auth import logout
from django.views import View

class CustomLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('/home')  # Redirect to your home page or any other page

    def post(self, request):
        logout(request)
        return redirect('create_question')
