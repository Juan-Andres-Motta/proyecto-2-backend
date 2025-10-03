import subprocess
from datetime import datetime

import typer
import uvicorn

app = typer.Typer()


@app.command()
def runserver(
    host: str = typer.Option("0.0.0.0", help="Host to bind the server to"),
    port: int = typer.Option(8000, help="Port to bind the server to"),
    reload: bool = typer.Option(True, help="Enable auto-reload"),
):
    """Run the FastAPI server."""
    typer.echo(f"Starting server on {host}:{port} with reload={reload}")
    uvicorn.run("app:app", host=host, port=port, reload=reload)


@app.command()
def makemigrations(
    message: str = typer.Option("Auto migration", help="Migration message")
):
    """Create a new Alembic migration."""
    date_prefix = datetime.now().strftime("%Y_%m_%d")
    full_message = f"{date_prefix}_{message}"
    typer.echo(f"Creating migration with message: {full_message}")
    result = subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", full_message],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        typer.echo("Migration created successfully")
        typer.echo(result.stdout)
    else:
        typer.echo("Error creating migration")
        typer.echo(result.stderr)


@app.command()
def migrate():
    """Apply all pending Alembic migrations."""
    typer.echo("Applying migrations...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"], capture_output=True, text=True
    )
    if result.returncode == 0:
        typer.echo("Migrations applied successfully")
        typer.echo(result.stdout)
    else:
        typer.echo("Error applying migrations")
        typer.echo(result.stderr)


@app.command()
def lint():
    """Run code quality tools: black, isort, and flake8."""
    typer.echo("Running code quality checks...")

    # Run black
    typer.echo("Formatting with Black...")
    result_black = subprocess.run(["black", "."], capture_output=True, text=True)
    if result_black.returncode == 0:
        typer.echo("Black formatting completed")
    else:
        typer.echo("Black formatting failed")
        typer.echo(result_black.stderr)

    # Run isort
    typer.echo("Sorting imports with isort...")
    result_isort = subprocess.run(["isort", "."], capture_output=True, text=True)
    if result_isort.returncode == 0:
        typer.echo("isort completed")
    else:
        typer.echo("isort failed")
        typer.echo(result_isort.stderr)

    # Run flake8
    typer.echo("Linting with flake8...")
    result_flake8 = subprocess.run(["flake8", "."], capture_output=True, text=True)
    if result_flake8.returncode == 0:
        typer.echo("flake8 passed")
    else:
        typer.echo("flake8 found issues")
        typer.echo(result_flake8.stdout)


if __name__ == "__main__":
    app()
