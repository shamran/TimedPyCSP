mkdir tmp
pdflatex -output-directory tmp skelet
cd tmp
#bibtex skelet 
cd ..
pdflatex  -interaction=batchmode -output-directory tmp skelet
pdflatex  -interaction=batchmode -output-directory tmp skelet
cp tmp/skelet.pdf ../masterthesis.pdf 
