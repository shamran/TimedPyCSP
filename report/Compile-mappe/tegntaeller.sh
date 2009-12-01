#! /bin/sh
echo "Tegn i skelet.pdf:"
pdftotext /home/dorte/speciale/Tekstudkast/compile-mappe/skelet.pdf - | egrep -E '\w\w\w+' | iconv -f ISO-8859-15 -t UTF-8 | wc -m
echo "specialet skal i alt fylde mellem 104.400 (60 sider) og 176.400 (80 sider) tegn
(Bemærk at tegntælleren tæller ALT med indholdsfortegnelse biblografi mm.)"