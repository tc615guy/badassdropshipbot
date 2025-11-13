#!/usr/bin/env python3
"""
Badass Dropship Bot - CLI Interface
"""
import asyncio
import sys
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from loguru import logger

from models.database import init_db, SessionLocal
from core import ProductScout, AIContentGenerator, MultiPlatformPublisher, AnalyticsEngine
from utils import SlackNotifier
from config import PRODUCT_CATEGORIES

# Setup
app = typer.Typer(
    name="badass-dropship",
    help="🚀 AI-powered dropshipping automation system",
    add_completion=False
)
console = Console()

# Configure logger
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)
logger.add("logs/dropship_{time}.log", rotation="1 day", retention="7 days")


@app.command()
def init():
    """Initialize database"""
    console.print("[bold green]Initializing database...[/bold green]")
    try:
        init_db()
        console.print("[bold green]✓ Database initialized successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]✗ Error: {e}[/bold red]")
        raise typer.Exit(1)


@app.command()
def scout(
    source: str = typer.Option("all", help="Source: all, aliexpress, cj, tiktok"),
    category: Optional[str] = typer.Option(None, help=f"Category: {', '.join(PRODUCT_CATEGORIES[:5])}..."),
    limit: int = typer.Option(50, help="Number of products to discover"),
    min_score: float = typer.Option(70.0, help="Minimum product score (0-100)"),
    save: bool = typer.Option(True, help="Save products to database")
):
    """🔍 Discover winning products"""
    console.print(f"\n[bold cyan]🔍 Scouting products from {source}...[/bold cyan]\n")

    async def run():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Discovering products...", total=None)

            scout_engine = ProductScout()
            products = await scout_engine.discover_products(
                source=source,
                category=category,
                limit=limit
            )

            # Filter by score
            products = [p for p in products if p.get("overall_score", 0) >= min_score]

            progress.update(task, completed=True)

        # Display results
        if not products:
            console.print("[yellow]No products found matching criteria[/yellow]")
            return

        table = Table(title=f"Found {len(products)} Products", show_header=True)
        table.add_column("Title", style="cyan", width=40)
        table.add_column("Source", style="magenta")
        table.add_column("Score", justify="right", style="green")
        table.add_column("Margin", justify="right", style="yellow")
        table.add_column("Price", justify="right")

        for p in products[:20]:  # Show first 20
            table.add_row(
                p.get("title", "")[:40],
                p.get("source", ""),
                f"{p.get('overall_score', 0):.1f}",
                f"{p.get('profit_margin', 0):.1f}%",
                f"${p.get('suggested_price', 0):.2f}"
            )

        console.print(table)

        # Save to database
        if save:
            from models.database import Product
            db = SessionLocal()

            saved_count = 0
            for product_data in products:
                existing = db.query(Product).filter(
                    Product.external_id == product_data.get("external_id"),
                    Product.source == product_data.get("source")
                ).first()

                if existing:
                    continue

                product = Product(
                    external_id=product_data.get("external_id"),
                    source=product_data.get("source"),
                    title=product_data.get("title"),
                    original_title=product_data.get("title"),
                    description=product_data.get("description", ""),
                    category=product_data.get("category"),
                    source_price=product_data.get("price", 0),
                    suggested_price=product_data.get("suggested_price", 0),
                    profit_margin=product_data.get("profit_margin", 0),
                    images=product_data.get("images", []),
                    rating=product_data.get("rating", 0),
                    review_count=product_data.get("reviews", 0),
                    orders=product_data.get("orders", 0),
                    trending_score=product_data.get("trending_score", 0),
                    overall_score=product_data.get("overall_score", 0)
                )
                db.add(product)
                saved_count += 1

            db.commit()
            db.close()

            console.print(f"\n[bold green]✓ Saved {saved_count} new products to database[/bold green]")

    asyncio.run(run())


@app.command()
def generate(
    product_id: int = typer.Argument(..., help="Product ID to generate content for"),
    variations: int = typer.Option(1, help="Number of variations to generate"),
):
    """✨ Generate AI-optimized content"""
    console.print(f"\n[bold cyan]✨ Generating AI content for product {product_id}...[/bold cyan]\n")

    async def run():
        db = SessionLocal()
        from models.database import Product

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            console.print(f"[bold red]✗ Product {product_id} not found[/bold red]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating content with Claude AI...", total=None)

            generator = AIContentGenerator()
            result = await generator.generate_complete_listing({
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "category": product.category,
                "price": product.source_price,
                "rating": product.rating,
                "images": product.images
            })

            # Update product
            product.ai_title = result.get("ai_title")
            product.ai_description = result.get("ai_description")
            product.ai_bullets = result.get("ai_bullets")
            product.seo_keywords = result.get("seo_keywords")
            product.status = "generated"

            from datetime import datetime
            product.generated_at = datetime.utcnow()

            db.commit()
            progress.update(task, completed=True)

        # Display results
        console.print("\n[bold green]✓ Content Generated![/bold green]\n")
        console.print(f"[bold]Original Title:[/bold] {product.title}")
        console.print(f"[bold]AI Title:[/bold] [cyan]{product.ai_title}[/cyan]\n")
        console.print(f"[bold]AI Description:[/bold]\n{product.ai_description[:200]}...\n")

        if product.ai_bullets:
            console.print("[bold]Key Features:[/bold]")
            for bullet in product.ai_bullets[:5]:
                console.print(f"  • {bullet}")

        db.close()

    asyncio.run(run())


@app.command()
def publish(
    product_id: int = typer.Argument(..., help="Product ID to publish"),
    platforms: List[str] = typer.Option(["tiktok"], help="Platforms to publish to")
):
    """📤 Publish product to platforms"""
    console.print(f"\n[bold cyan]📤 Publishing product {product_id}...[/bold cyan]\n")

    async def run():
        db = SessionLocal()
        from models.database import Product

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            console.print(f"[bold red]✗ Product {product_id} not found[/bold red]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Publishing to {', '.join(platforms)}...", total=None)

            publisher = MultiPlatformPublisher()
            results = await publisher.publish_product(
                {
                    "id": product.id,
                    "title": product.ai_title or product.title,
                    "ai_title": product.ai_title,
                    "description": product.ai_description or product.description,
                    "ai_description": product.ai_description,
                    "price": product.suggested_price or product.source_price,
                    "suggested_price": product.suggested_price,
                    "images": product.images,
                    "category": product.category
                },
                platforms,
                db
            )

            # Update status
            if any(results.values()):
                product.is_published = True
                product.status = "published"
                from datetime import datetime
                product.published_at = datetime.utcnow()
                db.commit()

            progress.update(task, completed=True)

        # Display results
        console.print("\n[bold green]✓ Publishing Complete![/bold green]\n")
        for platform, success in results.items():
            status = "[green]✓ Success[/green]" if success else "[red]✗ Failed[/red]"
            console.print(f"{platform}: {status}")

        db.close()

    asyncio.run(run())


@app.command()
def autopilot(
    sources: List[str] = typer.Option(["all"], help="Sources to scout"),
    platforms: List[str] = typer.Option(["tiktok"], help="Platforms to publish to"),
    category: Optional[str] = typer.Option(None, help="Product category"),
    min_score: float = typer.Option(70.0, help="Minimum product score"),
    limit: int = typer.Option(10, help="Number of products to process")
):
    """🚀 Full autopilot: discover → generate → publish"""
    console.print("\n[bold cyan]🚀 Starting Autopilot Mode...[/bold cyan]\n")
    console.print("[yellow]This will automatically discover, generate, and publish products[/yellow]\n")

    async def run():
        scout_engine = ProductScout()
        generator = AIContentGenerator()
        publisher = MultiPlatformPublisher()
        slack = SlackNotifier()
        db = SessionLocal()

        stats = {
            "discovered": 0,
            "generated": 0,
            "published": 0,
            "failed": 0
        }

        with Progress(console=console) as progress:
            # Step 1: Discover
            discover_task = progress.add_task("[cyan]Discovering products...", total=None)

            all_products = []
            for source in sources:
                products = await scout_engine.find_winning_products(
                    min_score=min_score,
                    sources=[source],
                    limit=limit
                )
                all_products.extend(products)

            stats["discovered"] = len(all_products)
            progress.update(discover_task, completed=True)

            # Step 2: Process each product
            for idx, product_data in enumerate(all_products[:limit], 1):
                process_task = progress.add_task(
                    f"[cyan]Processing {idx}/{min(limit, len(all_products))}: {product_data.get('title', '')[:30]}...",
                    total=None
                )

                try:
                    from models.database import Product

                    # Check if exists
                    existing = db.query(Product).filter(
                        Product.external_id == product_data.get("external_id"),
                        Product.source == product_data.get("source")
                    ).first()

                    if existing and existing.is_published:
                        progress.update(process_task, completed=True)
                        continue

                    # Save product
                    if not existing:
                        product = Product(
                            external_id=product_data.get("external_id"),
                            source=product_data.get("source"),
                            title=product_data.get("title"),
                            description=product_data.get("description", ""),
                            category=product_data.get("category"),
                            source_price=product_data.get("price", 0),
                            suggested_price=product_data.get("suggested_price", 0),
                            profit_margin=product_data.get("profit_margin", 0),
                            images=product_data.get("images", []),
                            rating=product_data.get("rating", 0),
                            orders=product_data.get("orders", 0),
                            overall_score=product_data.get("overall_score", 0)
                        )
                        db.add(product)
                        db.commit()
                        db.refresh(product)
                    else:
                        product = existing

                    # Generate content
                    generated = await generator.generate_complete_listing({
                        "id": product.id,
                        "title": product.title,
                        "description": product.description,
                        "category": product.category,
                        "price": product.source_price,
                        "rating": product.rating,
                        "images": product.images
                    })

                    product.ai_title = generated.get("ai_title")
                    product.ai_description = generated.get("ai_description")
                    product.ai_bullets = generated.get("ai_bullets")
                    product.status = "generated"
                    db.commit()
                    stats["generated"] += 1

                    # Publish
                    results = await publisher.publish_product(
                        {
                            "id": product.id,
                            "title": product.ai_title,
                            "description": product.ai_description,
                            "price": product.suggested_price,
                            "images": product.images,
                            "category": product.category
                        },
                        platforms,
                        db
                    )

                    if any(results.values()):
                        product.is_published = True
                        product.status = "published"
                        db.commit()
                        stats["published"] += 1

                except Exception as e:
                    logger.error(f"Error processing product: {e}")
                    stats["failed"] += 1

                progress.update(process_task, completed=True)

        # Summary
        console.print("\n[bold green]✓ Autopilot Complete![/bold green]\n")
        summary_table = Table(title="Results Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", justify="right", style="green")

        summary_table.add_row("Products Discovered", str(stats["discovered"]))
        summary_table.add_row("Content Generated", str(stats["generated"]))
        summary_table.add_row("Successfully Published", str(stats["published"]))
        summary_table.add_row("Failed", str(stats["failed"]))

        console.print(summary_table)

        db.close()

    asyncio.run(run())


@app.command()
def list(
    status: Optional[str] = typer.Option(None, help="Filter by status"),
    limit: int = typer.Option(20, help="Number of products to show")
):
    """📋 List products in database"""
    db = SessionLocal()
    from models.database import Product

    query = db.query(Product)

    if status:
        query = query.filter(Product.status == status)

    query = query.order_by(Product.overall_score.desc())
    products = query.limit(limit).all()

    if not products:
        console.print("[yellow]No products found[/yellow]")
        return

    table = Table(title=f"Products (showing {len(products)})")
    table.add_column("ID", style="cyan")
    table.add_column("Title", width=40)
    table.add_column("Source", style="magenta")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Published", justify="center")

    for p in products:
        table.add_row(
            str(p.id),
            p.title[:40],
            p.source,
            f"{p.overall_score:.1f}",
            p.status,
            "✓" if p.is_published else "✗"
        )

    console.print(table)
    db.close()


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(True, help="Enable auto-reload")
):
    """🌐 Start FastAPI server"""
    import uvicorn

    console.print(f"\n[bold green]🌐 Starting API server on http://{host}:{port}[/bold green]\n")

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


@app.command()
def stats():
    """📊 Show analytics dashboard"""
    db = SessionLocal()
    analytics = AnalyticsEngine()

    stats = analytics.get_dashboard_stats(db)

    console.print("\n[bold cyan]📊 Dashboard Statistics[/bold cyan]\n")

    # Products
    console.print("[bold]Products:[/bold]")
    console.print(f"  Total: {stats.get('products', {}).get('total', 0)}")
    console.print(f"  Discovered: {stats.get('products', {}).get('discovered', 0)}")
    console.print(f"  Published: {stats.get('products', {}).get('published', 0)}\n")

    # Listings
    console.print("[bold]Listings:[/bold]")
    console.print(f"  Total: {stats.get('listings', {}).get('total', 0)}")
    for platform, count in stats.get('listings', {}).get('by_platform', {}).items():
        console.print(f"  {platform}: {count}\n")

    # Revenue
    revenue = stats.get('revenue_30d', {})
    console.print("[bold]Revenue (Last 30 Days):[/bold]")
    console.print(f"  Total: ${revenue.get('total', 0):.2f}")
    console.print(f"  Orders: {revenue.get('orders', 0)}")
    console.print(f"  Avg Order Value: ${revenue.get('avg_order_value', 0):.2f}")

    db.close()


if __name__ == "__main__":
    app()
