from apis import create_app

app = create_app()
celery = app.celery_app  # pylint: disable=R0801
