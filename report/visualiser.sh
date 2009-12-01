mkdir tmp
pdflatex -output-directory tmp problemformulering
cd tmp
#bibtex skelet 
cd ..
pdflatex  -interaction=batchmode -output-directory tmp problemformulering 
pdflatex  -interaction=batchmode -output-directory tmp problemformulering 
cp tmp/problemformulering.pdf . 
