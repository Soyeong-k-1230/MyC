from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import Movie, Rating, Genre
from .forms import RatingForm

# Create your views here.
def index(request):
    movies = Movie.objects.order_by('-popularity')
    genres = Genre.objects.all()
    user_selected = []
    user_watched = []
    saved_unseen = []
    saved_cnt = 0
    ratings = []
    final_rec = []

    # 추천 알고리즘
    if request.user.is_authenticated:
        # 사용자가 찜한 영화
        selected_movies = request.user.selcted_movies.all()
        for movie in selected_movies:
            user_selected.append(movie)
        # 사용자가 본 영화
        watched_movies = request.user.watched_movies.all()
        for movie in watched_movies:
            user_watched.append(movie)
        if len(user_selected) or len(user_watched):
            # 1. 찜했는데 안본영화 나열
            for movie in selected_movies:
                if movie not in watched_movies:
                    saved_unseen.append(movie)
                
            if len(saved_unseen) > 10:
                saved_cnt = 10
            else:
                saved_cnt = len(saved_unseen)
            
            user_liked = []
            user_hated = []

            for movie in user_watched:
                ratings = movie.rating_set.all()
                if ratings:
                    for rating in ratings:
                        if request.user == rating.user:
                            if rating.rank == 1:
                                user_liked.append(rating.movie)
                            else:
                                user_hated.append(rating.movie)           
            year = ''
            year_dict = {}
            lang_dict = {}
            genre_dict = {}
            genre_dict_w = {}
            year_sorted = []
            lang_sorted = []
            genre_sorted = []
            genre_sorted_w = []

            cnt = 0
            while cnt <= 10:
                # 개봉 날짜별 추천 3개
                for movie in user_selected:
                    year = str(movie.release_date.year)
                    year = year[:3]
                    if year not in year_dict:
                        year_dict[year] = 1
                    else:
                        year_dict[year] += 1 
                year_sorted = sorted(year_dict.items(), key=lambda x: x[1], reverse=True)
                for i in range(3):
                    try:
                        movie_rec = Movie.objects.filter(release_date__startswith=year_sorted[i][0]).order_by('?')[0]
                        if movie_rec in saved_unseen or movie_rec in user_watched:
                            continue
                        if movie_rec in user_liked or movie_rec in user_hated:
                            continue
                        final_rec.append(movie_rec)
                        cnt += 1
                    except:
                        break
                    
                # 사용자가 본 영화 기준 언어 추천
                for movie in user_watched:
                    lang = movie.original_language
                    if lang not in lang_dict:
                        lang_dict[lang] = 1
                    else:
                        lang_dict[lang] += 1 
                if len(lang_sorted):
                    lang_sorted = sorted(lang_dict.items(), key=lambda x: x[1], reverse=True)
                    for i in range(3):
                        if i >= len(lang_sorted):
                            num = 0
                        else:
                            num = i
                        movie_rec = Movie.objects.filter(original_language=lang_sorted[num][0]).order_by('?')[0]
                        if movie_rec in saved_unseen or movie_rec in user_watched:
                            continue
                        if movie_rec in user_liked or movie_rec in user_hated:
                            continue
                        final_rec.append(movie_rec)
                        cnt += 1
                # 사용자가 저장한 영화 기준 장르 추천
                for movie in user_selected:
                    movie_genres = movie.genre_ids.all()
                    for genre in movie_genres:
                        if genre.name not in genre_dict:
                            genre_dict[genre.name] = 1
                        else:
                            genre_dict[genre.name] += 1
                    genre_sorted = sorted(genre_dict.items(), key=lambda x: x[1], reverse=True)
                for i in range(4):  
                    try: 
                        genre_rec = Genre.objects.get(name=genre_sorted[i][0])
                        movie_rec = genre_rec.movie_genres.all().order_by('?')[0]
                        if movie_rec in saved_unseen or movie_rec in user_watched:
                            continue
                        if movie_rec in user_liked or movie_rec in user_hated:
                            continue
                        final_rec.append(movie_rec)
                        cnt += 1
                    except:
                        break
                # 사용자가 본 영화 기준 장르 추천
                for movie in user_watched:
                    movie_genres = movie.genre_ids.all()
                    for genre in movie_genres:
                        if genre.name not in genre_dict_w:
                            genre_dict_w[genre.name] = 1
                        else:
                            genre_dict_w[genre.name] += 1
                    genre_sorted_w = sorted(genre_dict_w.items(), key=lambda x: x[1], reverse=True)
                for i in range(4):  
                    try: 
                        genre_rec = Genre.objects.get(name=genre_sorted_w[i][0])
                        movie_rec = genre_rec.movie_genres.all().order_by('?')[0]
                        if movie_rec in saved_unseen or movie_rec in user_watched:
                            continue
                        if movie_rec in user_liked or movie_rec in user_hated:
                            continue
                        final_rec.append(movie_rec)
                        cnt += 1
                    except:
                        break

    context = {
        'movie_top': movies[0],
        'movies_top3': movies[1:4],
        'saved_top_a' : saved_unseen[:5],
        'saved_top_b' : saved_unseen[5:10],
        'saved_cnt': saved_cnt,
        'final_rec': final_rec[:10],
        'final_top_a': final_rec[:5],
        'final_top_b': final_rec[5:10],
    }
    return render(request, 'movies/index.html', context)

def genre(request):
    movies = Movie.objects.all()
    genres = Genre.objects.all()
    context = {
        'movies': movies,
        'genres': genres,
    }
    return render(request, 'movies/genre.html', context)

def genre_filter(request, genre_pk):
    movies = Movie.objects.values('id').all()
    movies_cnt = len(movies)
    movies_list = [0] * movies_cnt
    genre = get_object_or_404(Genre, pk=genre_pk)
    movie_list = []
    hide_movie = []

    for movie in genre.movie_genres.all():
        movie_list.append(movie.id)

    for i in range(movies_cnt):
        if movies[i]['id'] not in movie_list:
            hide_movie.append(movies[i]['id'])

    context = {
        'hide_cnt': len(hide_movie), 
        'selected_movie': movie_list,
        'hide_movie': hide_movie,

    }
    return JsonResponse(context)

def movie_detail(request, movie_pk):
    movie = get_object_or_404(Movie, pk=movie_pk)
    ratings = movie.rating_set.order_by('-pk')
    movie_rank = [0] * 2
    movie_point = [0] * 5

    for rating in ratings:
        rank = rating.rank
        point = rating.standard
        if rank == 1:
            movie_rank[0] += 1
        else:
            movie_rank[1] += 1

        if point == 1:
            movie_point[0] += 1
        elif point == 2:
            movie_point[1] += 1
        elif point == 3:
            movie_point[2] += 1
        elif point == 4:
            movie_point[3] += 1
        else:
            movie_point[4] += 1
    
    rank_per = [0] * 2
    point_per = [0] * 5
    for i in range(2):
        if movie_rank[i] != 0:
            rank_per[i] = movie_rank[i] / sum(movie_rank) * 100

    for j in range(5):
        if movie_point[j] != 0:
            point_per[j] = movie_point[j] / sum(movie_point) * 100
    
    form = RatingForm()
    context = {
        'movie': movie,
        'ratings': ratings,
        'form': form,
        'rank_per': rank_per,
        'sum_rank': sum(movie_rank),
        'point_per': point_per,
        'sum_point': sum(movie_point),
    }
    return render(request, 'movies/movie_detail.html', context)

@require_POST
def rating_create(request, movie_pk):
    if request.user.is_authenticated:
        form = RatingForm(request.POST)
        movie = get_object_or_404(Movie, pk=movie_pk)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = request.user
            rating.movie = movie 
            rating.save()
            messages.success(request, '의견이 잘 반영되었습니다.')
            return redirect('movies:movie_detail', movie_pk)
    else:
        messages.info(request, 'Rating 작성을 위해서는 로그인이 필요합니다.')

        return redirect('accounts:login')

@login_required
def rating_update(request, movie_pk, rating_pk):
    rating = get_object_or_404(Rating, id=rating_pk)
    movie = get_object_or_404(Movie, pk=movie_pk)
    ratings = movie.rating_set.order_by('-pk')

    if request.user != rating.user:
        messages.error(request, '본인만 수정이 가능합니다.')
        return redirect('movies:movie_detail', movie_pk)
    
    if request.method =='POST':
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
            updated_rating = form.save(commit=False)
            updated_rating.save()
            messages.success(request, '의견이 수정되었습니다.')
            return redirect('movies:movie_detail', movie_pk)
    else:
        form = RatingForm(instance=rating)
    context = {
        'movie': movie,
        'ratings': ratings,
        'form': form,
    }
    return render(request, 'movies/movie_detail.html', context)

@login_required
@require_POST
def rating_delete(request, movie_pk, rating_pk):
    rating = get_object_or_404(Rating, pk=rating_pk)
    if request.user == rating.user:
        rating.delete()
        messages.success(request, '의견이 삭제되었습니다.')
    return redirect('movies:movie_detail', movie_pk)

def movie_select(request, movie_pk):
    movie = get_object_or_404(Movie, pk=movie_pk)

    s_count = 0
    select = False
    logged_out = True
    if request.user.is_authenticated:
        logged_out = False
        if movie.selected_users.filter(id=request.user.pk).exists():
            movie.selected_users.remove(request.user)
            select = False
        else:
            movie.selected_users.add(request.user)
            select = True
        s_count = request.user.selcted_movies.count()

    context = {
        'select': select,
        'user_saved_count': s_count,
        'count': movie.selected_users.count(),
        'logged_out': logged_out,
    }
    return JsonResponse(context)

def movie_watch(request, movie_pk):
    movie = get_object_or_404(Movie, pk=movie_pk)

    w_count = 0
    watch = False
    logged_out = True
    if request.user.is_authenticated:
        logged_out = False
        if movie.watched_users.filter(id=request.user.pk).exists():
            movie.watched_users.remove(request.user)
            watch = False
        else:
            movie.watched_users.add(request.user)
            watch = True
        w_count = request.user.watched_movies.count()
        # level change
        User = get_user_model()
        user = get_object_or_404(User, pk=request.user.id)
        if w_count >= 50:
            user.level = 2
            user.save()
        elif w_count >= 100:
            user.level = 3
            user.save()
        elif w_count >= 200:
            user.level = 4
            user.save()
        elif w_count >= 300:
            user.level = 5
            user.save()

    context = {
        'watch': watch,
        'user_watched_count': w_count,
        'count': movie.watched_users.count(),
        'logged_out': logged_out,
    }
    return JsonResponse(context)