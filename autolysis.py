import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import openai
import numpy as np
import httpx
import chardet
from collections import defaultdict
from google.colab import files

# Constants
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

class DatasetAnalyzer:
    """Class to handle dataset loading, analysis, and visualization."""

    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self.load_data()

    def load_data(self):
        """Load dataset with inferred encoding."""
        with open(self.file_path, 'rb') as f:
            raw_data = f.read()

        # Detect encoding using chardet or charset_normalizer
        encoding = chardet.detect(raw_data)['encoding']
        if not encoding:
            encoding = "utf-8"  # Fallback to UTF-8 if encoding is not detected

        # Load the CSV file with the detected encoding
        return pd.read_csv(self.file_path, encoding=encoding)

    def analyze(self):
        """Perform dataset analysis."""
        numeric_data = self.data.select_dtypes(include='number')
        summary = defaultdict(dict)
        summary['summary'] = self.data.describe(include='all').to_dict()
        summary['missing_values'] = self.data.isnull().sum().to_dict()
        if not numeric_data.empty:
            summary['correlation'] = numeric_data.corr().to_dict()
        return summary

    def visualize(self):
        """Generate visualizations for numeric data."""
        numeric_columns = self.data.select_dtypes(include='number').columns
        sns.set_theme(style="darkgrid")

        for col in numeric_columns:
            plt.figure(figsize=(6, 4))
            sns.histplot(self.data[col].dropna(), kde=True, color="blue")
            plt.title(f"Distribution of {col}")
            plt.xlabel(col)
            plt.ylabel("Frequency")
            plt.show()
            plt.savefig(f'{col}_distribution.png')

class NarrativeGenerator:
    """Class to handle narrative generation using the AI Proxy."""

    def __init__(self, api_url, api_token):
        self.api_url = api_url
        self.api_token = api_token

    def generate(self, analysis):
        """Generate narrative using the API."""
        if not self.api_token:
            raise EnvironmentError("AIPROXY_TOKEN environment variable not set.")

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        prompt = f"Analyze and narrate based on the following data: {analysis}"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = httpx.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error during narrative generation: {e}")
            return "Narrative generation failed."


def main():
    """Main function to process the dataset."""
    # Step 1: File Upload
    uploaded = files.upload()
    file_path = list(uploaded.keys())[0]

    print(f"Processing dataset: {file_path}")

    # Step 2: Analyze the dataset
    analyzer = DatasetAnalyzer(file_path)
    analysis = analyzer.analyze()
    print("Data analysis complete.")

    # Step 3: Visualize the dataset
    print("Generating visualizations...")
    analyzer.visualize()

    # Step 4: Generate narrative
    generator = NarrativeGenerator(API_URL, AIPROXY_TOKEN)
    narrative = generator.generate(analysis)
    print("Narrative generation complete.")

    # Step 5: Display narrative
    print("\n### Narrative Generated ###\n")
    print(narrative)

    with open('README.md', 'w') as f:
        f.write(narrative)


# Run the script in Colab
if __name__ == "__main__":
    main()
