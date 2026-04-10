import csv

with open("./budapest_data/routes.txt", encoding="utf-8", newline="") as f_in:
    reader = csv.DictReader(f_in)
    
    with open("routes_out.txt", "w", encoding="utf-8") as f_out:
        for line in reader:
            f_out.write(f"{line['route_id']}: {line['route_short_name']}\n")