import io
import nltk
import PyPDF2

from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
from nltk.tokenize import RegexpTokenizer
from nltk.stem import PorterStemmer
from nltk.cluster.util import cosine_distance
from operator import itemgetter

# Set up NLTK
nltk.download('punkt')
nltk.download('stopwords')

# Function to preprocess text
def preprocess_text(text):
    # Tokenize text into sentences
    sentences = sent_tokenize(text)

    # Tokenize each sentence into words
    words = []
    for sentence in sentences:
        # Remove punctuation and convert to lowercase
        tokenizer = RegexpTokenizer(r'\w+')
        words += [word.lower() for word in tokenizer.tokenize(sentence)]

    # Remove stop words
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words]

    # Stem words
    stemmer = PorterStemmer()
    words = [stemmer.stem(word) for word in words]

    return words

# Function to calculate similarity between two sentences
def sentence_similarity(sent1, sent2):
    # Convert sentences to sets of words
    sent1 = set(sent1)
    sent2 = set(sent2)

    # Calculate Jaccard similarity coefficient
    return len(sent1.intersection(sent2)) / len(sent1.union(sent2))

# Function to generate summary
def generate_summary(text, num_sentences):
    # Preprocess text
    words = preprocess_text(text)

    # Create frequency distribution of words
    freq_dist = FreqDist(words)

    # Create list of unique words
    word_list = list(set(words))

    # Create matrix of sentence similarities
    similarity_matrix = []
    for i in range(len(word_list)):
        row = []
        for j in range(len(word_list)):
            if i == j:
                row.append(0)
            else:
                row.append(sentence_similarity(word_list[i], word_list[j]))
        similarity_matrix.append(row)

    # Use TextRank algorithm to identify most important sentences
    scores = {}
    for i in range(len(word_list)):
        score = 0
        for j in range(len(word_list)):
            score += similarity_matrix[i][j] * freq_dist[word_list[j]]
        scores[word_list[i]] = score

    top_sentences = sorted(scores.items(), key=itemgetter(1), reverse=True)[:num_sentences]

    # Combine top sentences to form summary
    summary = ''
    for sentence in top_sentences:
        summary += sentence[0] + ' '

    return summary

# Function to read PDF file
def read_pdf_file(filename):
    # Open PDF file
    with open(filename, 'rb') as f:
        # Read PDF file into PyPDF2 object
        pdf_reader = PyPDF2.PdfFileReader(f)
        # Extract text from PDF pages
        text = ''
        for page_num in range(pdf_reader.numPages):
            page = pdf_reader.getPage(page_num)
            text += page.extractText()

    return text

filename = 'disaster-management.pdf'
num_sentences = 3
text = read_pdf_file(filename)
summary = generate_summary(text, num_sentences)
print(summary)
