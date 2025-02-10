import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Movie(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    release_year = Column(Integer)
    genre_id = Column(Integer, ForeignKey('genres.id'))
    genre = relationship("Genre", back_populates="movies")

class Genre(Base):
    __tablename__ = 'genres'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    movies = relationship("Movie", back_populates="genre")

engine = create_engine('sqlite:///movie_database.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

class GenreType(SQLAlchemyObjectType):
    class Meta:
        model = Genre
        interfaces = (graphene.relay.Node,)

class MovieType(SQLAlchemyObjectType):
    class Meta:
        model = Movie
        interfaces = (graphene.relay.Node,)

class CreateGenre(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)

    genre = graphene.Field(lambda: GenreType)

    def mutate(self, info, name):
        genre = Genre(name=name)
        session.add(genre)
        session.commit()
        return CreateGenre(genre=genre)

class UpdateGenre(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String(required=True)

    genre = graphene.Field(lambda: GenreType)

    def mutate(self, info, id, name):
        genre = session.query(Genre).filter_by(id=id).first()
        if genre:
            genre.name = name
            session.commit()
        return UpdateGenre(genre=genre)

class DeleteGenre(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        genre = session.query(Genre).filter_by(id=id).first()
        if genre:
            session.delete(genre)
            session.commit()
            return DeleteGenre(ok=True)
        return DeleteGenre(ok=False)

class CreateMovie(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        description = graphene.String()
        release_year = graphene.Int()
        genre_id = graphene.Int(required=True)

    movie = graphene.Field(lambda: MovieType)

    def mutate(self, info, title, description, release_year, genre_id):
        movie = Movie(
            title=title,
            description=description,
            release_year=release_year,
            genre_id=genre_id
        )
        session.add(movie)
        session.commit()
        return CreateMovie(movie=movie)

class UpdateMovie(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        title = graphene.String(required=True)
        description = graphene.String()
        release_year = graphene.Int()
        genre_id = graphene.Int(required=True)

    movie = graphene.Field(lambda: MovieType)

    def mutate(self, info, id, title, description, release_year, genre_id):
        movie = session.query(Movie).filter_by(id=id).first()
        if movie:
            movie.title = title
            movie.description = description
            movie.release_year = release_year
            movie.genre_id = genre_id
            session.commit()
        return UpdateMovie(movie=movie)

class DeleteMovie(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    ok = graphene.Boolean()

    def mutate(self, info, id):
        movie = session.query(Movie).filter_by(id=id).first()
        if movie:
            session.delete(movie)
            session.commit()
            return DeleteMovie(ok=True)
        return DeleteMovie(ok=False)

class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_genres = SQLAlchemyConnectionField(GenreType)
    all_movies = SQLAlchemyConnectionField(MovieType)
    get_movies_by_genre = graphene.List(MovieType, genre_id=graphene.Int(required=True))
    get_genres_by_movie = graphene.List(GenreType, movie_id=graphene.Int(required=True))

    def resolve_get_movies_by_genre(self, info, genre_id):
        return session.query(Movie).filter_by(genre_id=genre_id).all()

    def resolve_get_genres_by_movie(self, info, movie_id):
        movie = session.query(Movie).filter_by(id=movie_id).first()
        if movie:
            return [movie.genre]
        return []

class Mutation(graphene.ObjectType):
    create_genre = CreateGenre.Field()
    update_genre = UpdateGenre.Field()
    delete_genre = DeleteGenre.Field()
    create_movie = CreateMovie.Field()
    update_movie = UpdateMovie.Field()
    delete_movie = DeleteMovie.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

if __name__ == '__main__':
    from flask import Flask
    from flask_graphql import GraphQLView

    app = Flask(__name__)
    app.debug = True
    app.add_url_rule(
        '/graphql',
        view_func=GraphQLView.as_view(
            'graphql',
            schema=schema,
            graphiql=True
        )
    )
    app.run()



