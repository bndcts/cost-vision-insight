#!/bin/bash
# Quick script to check articles in the database

echo "=== Checking Articles in Database ==="
echo ""

docker exec -it cost-vision-insight-cost-model-db-1 psql -U postgres -d cost_model -c "
SELECT 
    id, 
    article_name, 
    description,
    product_specification_filename,
    drawing_filename,
    comment,
    created_at 
FROM articles 
ORDER BY id DESC 
LIMIT 10;"

echo ""
echo "=== Total Article Count ==="
docker exec -it cost-vision-insight-cost-model-db-1 psql -U postgres -d cost_model -c "
SELECT COUNT(*) as total_articles FROM articles;"

