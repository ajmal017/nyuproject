Download Requirements:
sudo apt-get install g++

pip install numpy
pip install scipy
pip install pybind
pip install fasttext

Documentation: https://pypi.org/project/fasttext/

training_data_i_scraped.csv - 3000 CSR news with Category Labels scraped from https://www.csrwire.com/home/more_news 
Used to create training data
categ.train - Data for Training the model
categ.valid - Data for Testing the model
ESG_catgories.txt - ESG issue category labels for classifying
model_categ.bin - the model used for issue identification

analtext.py - use to interact with model, input text for classification

Run the code in terminal:
python analtext.py
