"""
Example workflow demonstrating the full pipeline
"""
import asyncio
from models.database import init_db, SessionLocal, Product
from core import ProductScout, AIContentGenerator, MultiPlatformPublisher
from utils import SlackNotifier


async def example_manual_workflow():
    """
    Example: Manual workflow - discover → generate → publish
    """
    print("🚀 Example: Manual Product Pipeline\n")

    # Initialize
    init_db()
    db = SessionLocal()

    scout = ProductScout()
    generator = AIContentGenerator()
    publisher = MultiPlatformPublisher()
    slack = SlackNotifier()

    # Step 1: Discover products
    print("Step 1: Discovering products from AliExpress...")
    products = await scout.discover_products(
        source="aliexpress",
        category="electronics",
        limit=10
    )

    # Filter for high-scoring products
    winning_products = [p for p in products if p.get("overall_score", 0) >= 80]

    print(f"Found {len(winning_products)} winning products\n")

    if not winning_products:
        print("No winning products found. Try lowering the score threshold.")
        return

    # Take the best product
    best_product = winning_products[0]
    print(f"Selected: {best_product.get('title')}")
    print(f"Score: {best_product.get('overall_score')}")
    print(f"Profit Margin: {best_product.get('profit_margin')}%\n")

    # Step 2: Save to database
    print("Step 2: Saving to database...")
    product = Product(
        external_id=best_product.get("external_id"),
        source=best_product.get("source"),
        title=best_product.get("title"),
        description=best_product.get("description", ""),
        category=best_product.get("category"),
        source_price=best_product.get("price", 0),
        suggested_price=best_product.get("suggested_price", 0),
        profit_margin=best_product.get("profit_margin", 0),
        images=best_product.get("images", []),
        rating=best_product.get("rating", 0),
        review_count=best_product.get("reviews", 0),
        orders=best_product.get("orders", 0),
        overall_score=best_product.get("overall_score", 0)
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    print(f"✓ Saved as product ID: {product.id}\n")

    # Step 3: Generate AI content
    print("Step 3: Generating AI-optimized content...")
    generated = await generator.generate_complete_listing({
        "id": product.id,
        "title": product.title,
        "description": product.description,
        "category": product.category,
        "price": product.source_price,
        "rating": product.rating,
        "images": product.images
    })

    # Update product
    product.ai_title = generated.get("ai_title")
    product.ai_description = generated.get("ai_description")
    product.ai_bullets = generated.get("ai_bullets")
    product.seo_keywords = generated.get("seo_keywords")
    product.status = "generated"
    db.commit()

    print(f"✓ Generated content")
    print(f"  AI Title: {product.ai_title}\n")

    # Step 4: Publish to TikTok
    print("Step 4: Publishing to TikTok...")
    results = await publisher.publish_product(
        {
            "id": product.id,
            "title": product.ai_title,
            "description": product.ai_description,
            "price": product.suggested_price,
            "images": product.images,
            "category": product.category
        },
        ["tiktok"],
        db
    )

    if results.get("tiktok"):
        product.is_published = True
        product.status = "published"
        db.commit()
        print("✓ Published successfully!\n")

        # Send Slack notification
        await slack.notify_listing_published(
            {
                "title": product.ai_title,
                "suggested_price": product.suggested_price,
                "profit_margin": product.profit_margin
            },
            results
        )
    else:
        print("✗ Publishing failed\n")

    db.close()
    print("✓ Workflow complete!")


async def example_batch_processing():
    """
    Example: Process multiple products in batch
    """
    print("🚀 Example: Batch Processing\n")

    init_db()
    db = SessionLocal()

    scout = ProductScout()
    generator = AIContentGenerator()
    publisher = MultiPlatformPublisher()

    # Discover multiple products
    print("Discovering products...")
    products = await scout.find_winning_products(
        min_score=75.0,
        sources=["all"],
        limit=20
    )

    print(f"Found {len(products)} products to process\n")

    # Process in batches of 5
    batch_size = 5
    for i in range(0, len(products), batch_size):
        batch = products[i:i + batch_size]

        print(f"Processing batch {i//batch_size + 1}...")

        for product_data in batch:
            # Save product
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
                description=product_data.get("description", ""),
                category=product_data.get("category"),
                source_price=product_data.get("price", 0),
                suggested_price=product_data.get("suggested_price", 0),
                profit_margin=product_data.get("profit_margin", 0),
                images=product_data.get("images", []),
                overall_score=product_data.get("overall_score", 0)
            )
            db.add(product)

        db.commit()
        print(f"  ✓ Batch saved\n")

    db.close()
    print("✓ Batch processing complete!")


async def example_competitor_analysis():
    """
    Example: Analyze competitor store
    """
    print("🚀 Example: Competitor Analysis\n")

    scout = ProductScout()

    competitor_url = "https://example-competitor-store.com"

    print(f"Analyzing: {competitor_url}...")
    analysis = await scout.analyze_competitor(competitor_url)

    print("\nResults:")
    print(f"  Products found: {analysis.get('product_count', 0)}")
    print(f"  Average price: ${analysis.get('avg_price', 0):.2f}")

    if analysis.get('top_categories'):
        print("\n  Top categories:")
        for category, count in analysis.get('top_categories', [])[:5]:
            print(f"    - {category}: {count} products")

    print("\n✓ Analysis complete!")


async def example_ab_testing():
    """
    Example: Generate variations for A/B testing
    """
    print("🚀 Example: A/B Testing\n")

    init_db()
    db = SessionLocal()
    generator = AIContentGenerator()

    # Get a product
    product = db.query(Product).first()

    if not product:
        print("No products in database. Run discovery first.")
        return

    print(f"Generating 3 variations for: {product.title}\n")

    variations = await generator.generate_variations(
        {
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "category": product.category,
            "price": product.source_price
        },
        count=3
    )

    for i, variant in enumerate(variations, 1):
        print(f"Variation {i}:")
        print(f"  Title: {variant.get('ai_title')}")
        print(f"  Description: {variant.get('ai_description', '')[:100]}...")
        print()

    db.close()
    print("✓ Variations generated!")


if __name__ == "__main__":
    print("Select example to run:")
    print("1. Manual workflow (discover → generate → publish)")
    print("2. Batch processing")
    print("3. Competitor analysis")
    print("4. A/B testing")
    print()

    choice = input("Enter number (1-4): ")

    if choice == "1":
        asyncio.run(example_manual_workflow())
    elif choice == "2":
        asyncio.run(example_batch_processing())
    elif choice == "3":
        asyncio.run(example_competitor_analysis())
    elif choice == "4":
        asyncio.run(example_ab_testing())
    else:
        print("Invalid choice")
