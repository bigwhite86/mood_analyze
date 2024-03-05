# 需要安裝transformers
# pip install transformers

import torch
import torch.nn as nn
from transformers import BertTokenizer, BertForSequenceClassification
from flask import Flask, render_template

app = Flask(__name__)

class ColorPredictor:
    def __init__(self, model_path="trained_model_0205.pth"):
        self.model = BertForSequenceClassification.from_pretrained('bert-base-chinese', num_labels=4)
        self.model.load_state_dict(torch.load(model_path))
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')

    def predict_colors(self, texts):
        self.model.eval()
        color_probabilities_list = []

        for text in texts:
            encoded_dict_test = self.tokenizer.encode_plus(
                text,
                add_special_tokens=True,
                max_length=512,
                padding='max_length',
                truncation=True,
                return_attention_mask=True,
                return_tensors='pt',
            )

            input_ids = encoded_dict_test['input_ids']
            attention_mask = encoded_dict_test['attention_mask']

            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)

            logits = outputs.logits
            probabilities = nn.functional.softmax(logits, dim=1)
            color_probabilities = probabilities[0].tolist()
            color_probabilities_list.append({
                "紅色機率": color_probabilities[0],
                "黃色機率": color_probabilities[1],
                "藍色機率": color_probabilities[2],
                "綠色機率": color_probabilities[3]
            })

        return color_probabilities_list


@app.route('/color_prediction')
def color_prediction():
    # 假設 color_probabilities_list 和 file_content 是從某處獲取的數據
    # 此處為假數據，您應該根據實際情況更改
    color_predictor = ColorPredictor()
    color_probabilities_list = color_predictor.predict_colors(["這是一個示例文本。"])
    file_content = "這是檔案的內容..."  # 檔案內容
    return render_template('color_prediction.html', color_probabilities_list=color_probabilities_list, file_content=file_content)


if __name__ == '__main__':
    app.run(debug=True)
