import csv

with open("./budapest_data/stops.txt", encoding="utf-8", newline="") as f_in:
    reader = csv.DictReader(f_in)
    
    with open("stops_out.txt", "w", encoding="utf-8") as f_out:
        for line in reader:
            f_out.write(f"{line['stop_id']}: {line['stop_name']}\n")

