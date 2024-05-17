# CS6910_assignment3
IIT Madras Deep Learning assignment 3

## Encoder
The encoder is a simple cell of either LSTM, RNN or GRU. The input to the encoder is a sequence of characters and the output is a sequence of hidden states. The hidden state of the last time step is used as the context vector for the decoder.

## Decoder
The decoder is again a simple cell of either LSTM, RNN or GRU. The input to the decoder is the hidden state of the encoder and the output of the previous time step. The output of the decoder is a sequence of characters. The decoder has an additional fully connected layer and a log softmax which is used to predict the next character.

## Attention Mechanism
The attention mechanism is implemented using the dot product attention mechanism. The attentions are calulated by a weighted sum of softmax values of dot products of the hidden states of the decoder and the hidden states of the encoder. The attention values are then concatenated with the hidden states of the decoder and passed through a fully connected layer to get the output of the decoder.

## Dataset
The dataset used is the Aksharankar Dataset provided by the course. The dataset contains 3 files, namely, `train.csv`, `valid.csv` and `test.csv` for each language for a subset of indian languages. I have used the Tamil dataset for this assignment. The dataset contains 2 columns, namely, `English` and `Hindi` words which are the input and output strings respectively.

Implemented a Encoder Decoder Architecture with and without Attention Mechanism and used then to perform Transliteration on the Akshanrankar Dataset provided. These models where built using RNN, LSTM and GRU cells provided by PyTorch.

Question 1 : It is about encoder decoder model making , the codefile has been added to the  github repo , and the answers of the questions are given in  the wandb report

Question 2 : It is about running sweeps after making the encoder decoder model . The hyperparameter choice strategy is mentioned in the wandb report and the codefile is uploaded in github

Question 3 : This is about making inferences from the available plots (from the sweep run on question 2), The details are written in the wandb report.

Question 5 : This question is about introducing attention layer in our seq2seq model . The necessery plots are uploaded in report and the codefile is uploaded in github repo

Link to the wandb report is = [https://wandb.ai/vishnukundhan333/CS6910_assignment3/reports/DL-Assignment-3--Vmlldzo3OTkzMjcx/edit](https://wandb.ai/vishnukundhan333/CS6910_assignment3/reports/DL-Assignment-3--Vmlldzo3OTc3Njcw)
