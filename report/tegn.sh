pdftotext masterthesis.pdf - | egrep -e '\w\w+' | iconv -f ISO-8859-15 -t UTF-8 | wc -m
