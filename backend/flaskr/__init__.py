import os
import sys

from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app)

    @app.route("/")
    @cross_origin()
    def hello():
        return jsonify({'message': 'HELLO WORLD'})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route("/categories")
    def retrieve_categories():
        category_query = Category.query.order_by(Category.id).all()
        categories = {}
        for category in category_query:
            categories[category.id] = category.type

        if len(categories) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "categories": categories,
                "total_categories": len(categories),
            }
        )

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route("/questions")
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        category_query = Category.query.order_by(Category.id).all()
        categories = {}
        for category in category_query:
            categories[category.id] = category.type

        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "categories": categories,
                "total_questions": len(Question.query.all()),
            }
        )

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route("/questions/<int:question_id>", methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.filter_by(id=question_id).one_or_none()
        try:
            if question is None:
                abort(404)
            question.delete()
            return jsonify({
                "success": True,
                "deleted": question_id
            })
        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route("/questions", methods=['POST'])
    def add_question():
        try:
            body = request.get_json()
            error = False
            question = body.get("question", None)
            answer = body.get("answer", None)
            difficulty = body.get("difficulty", None)
            category = body.get("category", None)
            question = Question(question=question,
                                answer=answer,
                                difficulty=difficulty,
                                category=category,
                                )
            question.insert()
            questions = question.query.all()
            total_questions = len(questions)
            created = question.id
        except:
            error = True
            print(sys.exc_info())

        if error:
            abort(400)
        else:
            return jsonify({
                'success': True,
                'created': created,
                'total_questions': total_questions

            })

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route("/questions/search/", methods=['POST'])
    def search_questions():
        body = request.get_json()
        searchTerm = body.get("searchTerm", '')
        search = f"%{searchTerm}%"
        selection = Question.query.filter(Question.question.ilike(search))
        current_questions = paginate_questions(request, selection)
        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "total_questions": len(current_questions),
            }
        )

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route("/categories/<int:category_id>/questions")
    def retrieve_questions_by_category(category_id):
        error = False
        current_questions = 0
        try:
            selection = Question.query.filter_by(category=str(category_id))
            current_questions = paginate_questions(request, selection)
            category_query = Category.query.order_by(Category.id).all()
            current_category = Category.query.filter_by(id=str(category_id)).one_or_none().format()
            categories = {}
            for category in category_query:
                categories[category.id] = category.type
        except:
            error = True
            print(sys.exc_info())

        if error:
            abort(400)

        if len(current_questions) == 0:
            abort(404)

        return jsonify(
            {
                "success": True,
                "questions": current_questions,
                "categories": categories,
                "current_category": current_category,
                "total_questions": len(current_questions),
            }
        )

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route("/quizzes", methods=['POST'])
    def quizzes():
        body = request.get_json()
        if not body:
            abort(400)
        quizz_category = body.get('quiz_category')

        category_id = quizz_category['id']
        previous_questions = body.get('previous_questions')
        available_question = []
        try:
            if category_id == 0:
                all_question = Question.query.all()
                for question in all_question:
                    question_id = question.id
                    available_question.append(question_id)
                if not previous_questions:
                    current_question = Question.query.filter_by(
                        id=random.choice(available_question)).one_or_none().format()
                else:
                    for question in previous_questions:
                        for i in available_question:
                            if question == i:
                                available_question.remove(question)
                    current_question = Question.query.filter_by(
                        id=random.choice(available_question)).one_or_none().format()
            else:
                all_question_by_category = Question.query.filter_by(category=str(category_id)).all()
                for question in all_question_by_category:
                    question_id = question.id
                    available_question.append(question_id)
                if not previous_questions:

                    current_question = Question.query.filter_by(
                        id=random.choice(available_question)).one_or_none().format()
                else:
                    for question in previous_questions:
                        for i in available_question:
                            if question == i:
                                available_question.remove(question)
                    current_question = Question.query.filter_by(
                        id=random.choice(available_question)).one_or_none().format()
        except:
            current_question = None

        return jsonify(
            {
                "success": True,
                "question": current_question,
            }
        )

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "Internal Server Error"
        }), 500

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable action"
        }), 422

    @app.errorhandler(405)
    def unauthorized(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method not allow"
        }), 405

    @app.errorhandler(400)
    def unauthorized(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad Request"
        }), 400

    return app
