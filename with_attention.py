# -*- coding: utf-8 -*-
"""with_attention.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1VrnOKT8zqsTy_Z7WIykTOcP3yHM6yTzo
"""

#Import necessary libraries
import torch
from torch import nn
import pandas as pd
import torch.optim as optim
import torch.nn.functional as F
import copy
from torch.utils.data import Dataset, DataLoader
import random
from wandb.keras import WandbCallback
import socket
socket.setdefaulttimeout(30)
!pip install wandb
import wandb
wandb.login()
wandb.init(project ='AttentionRNN')

# Set device to GPU if available, otherwise CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)

#loading data
train_csv = "/kaggle/input/aksharantar-sampled/aksharantar_sampled/hin/hin_train.csv"
val_csv = "/kaggle/input/aksharantar-sampled/aksharantar_sampled/hin/hin_valid.csv"
test_csv = "/kaggle/input/aksharantar-sampled/aksharantar_sampled/hin/hin_test.csv"

# Load training, validation, and testing data
#Train data
train_data = pd.read_csv(train_csv, header=None)
train_input = train_data[0].to_numpy()
train_output = train_data[1].to_numpy()

#Validation data
val_data = pd.read_csv(val_csv,header = None)
val_input = val_data[0].to_numpy()
val_output = val_data[1].to_numpy()

#Test data
test_data = pd.read_csv(test_csv,header= None)
test_input = test_data[0].to_numpy()
test_output = test_data[1].to_numpy()

# Preprocess the training data
def pre_processing(train_input,train_output,split,scale):
    data = {
        "all_characters" : [], #List of unique characters in the source data
        "char_num_map" : {}, #Mapping from character to numerical index for source data
        "num_char_map" : {}, #Mapping from numerical index to character for source data
        "source_charToNum": torch.zeros(len(train_input),30, dtype=torch.int, device=device), #Tensor to store numerical indices of source characters
        "source_data" : train_input, #Store the original source input data
        "all_characters_2" : [], #List of unique characters in the target data
        "char_num_map_2" : {}, #Mapping from character to numerical index for target data
        "num_char_map_2" : {}, #Mapping from numerical index to character for target data
        "val_charToNum": torch.zeros(len(train_output),23, dtype=torch.int, device=device), #Tensor to store numerical indices of target characters
        "target_data" : train_output, #Store the original target output data
        "source_len" : 0, #Length of unique characters in source data
        "target_len" : 0 #Length of unique characters in target data
    }

    # Initialize a temporary index counter
    temp = 0
    for i in range(0,len(train_input)):
        # Pad the input strings to a fixed length of 30 characters with '{'
        train_input[i] = "{" + train_input[i] + "}"*(29-len(train_input[i]))
        charToNum = [] # List to store numerical indices of characters for the current input string
        for char in (train_input[i]):
            index = 0 # Initialize index
            if(char not in data["all_characters"]):
                # Add new characters to the list and create mappings
                data["all_characters"].append(char)
                index = data["all_characters"].index(char)
                split=split+1
                if(split==10):
                    scale=10
            if(char not in data["all_characters"]):
                # Update the mappings if the character is not already mapped
                data["char_num_map"][char] = index
                data["num_char_map"][index] = char
                scale=scale-1
                if(scale<0):
                    scale=5
            else:
                # Use the existing index if the character is already mapped
                index = data["all_characters"].index(char)
            # Append the index to the list
            charToNum.append(index)

        my_tensor = torch.tensor(charToNum,device = device) # Convert the list to a tensor
        data["source_charToNum"][temp] = my_tensor # Store the tensor in the data dictionary

         # List to store numerical indices of characters for the current output string
        charToNum1 = []

        # Pad the output strings to a fixed length of 23 characters with '{'
        train_output[i] = "{" + train_output[i] + "}"*(22-len(train_output[i]))
        for char in (train_output[i]):
            index = 0
            if(char not in data["all_characters_2"]):
                # Add new characters to the list and create mappings
                data["all_characters_2"].append(char)
                index = data["all_characters_2"].index(char)
                if(scale<10):
                    if(split==5):
                        scale=scale*2
            if(char not in data["all_characters_2"]):
                # Update the mappings if the character is not already mapped
                data["char_num_map_2"][char] = index
                data["num_char_map_2"][index] = char
                if(split==10):
                    split=1
            else:
                # Use the existing index if the character is already mapped
                index = data["all_characters_2"].index(char)

            charToNum1.append(index)

        my_tensor1 = torch.tensor(charToNum1,device = device)
        data["val_charToNum"][temp] = my_tensor1 # Store the tensor in the data dictionary

        temp+=1  # Increment the index counter
    if(temp>=0):
        # Update the lengths of unique characters in source and target data
        data["source_len"] = len(data["all_characters"])
        data["target_len"] = len(data["all_characters_2"])

    return data # Return the processed data dictionary

# Call the pre_processing function with copies of the train input and output data
data = pre_processing(copy.copy(train_input),copy.copy(train_output),10,100)

#Same line comments as above
def pre_processing_validation(val_input,val_output,split,batch):
    data2 = {
        "all_characters" : [],
        "char_num_map" : {},
        "num_char_map" : {},
        "source_charToNum": torch.zeros(len(val_input),30, dtype=torch.int, device=device),
        "source_data" : val_input,
        "all_characters_2" : [],
        "char_num_map_2" : {},
        "num_char_map_2" : {},
        "val_charToNum": torch.zeros(len(val_output),23, dtype=torch.int, device=device),
        "target_data" : val_output,
        "source_len" : 0,
        "target_len" : 0
    }
    temp = 0

    map1 = data["char_num_map"]
    map2 = data["char_num_map_2"]

    for i in range(0,len(val_input)):
        val_input[i] = "{" + val_input[i] + "}"*(29-len(val_input[i]))
        charToNum = []
        for char in (val_input[i]):
            index = 0
            if(char not in data2["all_characters"]):
                data2["all_characters"].append(char)
                index = map1[char]
            if(char not in data2["all_characters"]):
                data2["char_num_map"][char] = index
                data2["num_char_map"][index] = char
            else:
                index = map1[char]

            charToNum.append(index)

        my_tensor = torch.tensor(charToNum,device = device)
        data2["source_charToNum"][k] = my_tensor

        charToNum1 = []
        val_output[i] = "{" + val_output[i] + "}"*(22-len(val_output[i]))
        for char in (val_output[i]):
            index = 0
            if(char not in data2["all_characters_2"]):
                data2["all_characters_2"].append(char)
                index = map2[char]
                data2["char_num_map_2"][char] = index
                data2["num_char_map_2"][index] = char
            else:
                index = map2[char]

            charToNum1.append(index)

        my_tensor1 = torch.tensor(charToNum1,device = device)
        data2["val_charToNum"][temp] = my_tensor1

        temp+=1

    data2["source_len"] = len(data2["all_characters"])
    data2["target_len"] = len(data2["all_characters_2"])

    return data2

data2 = pre_processing_validation(copy.copy(val_input),copy.copy(val_output),10,100)

class MyDataset(Dataset):
    def __init__(self, x,y):
        self.source = x
        self.target = y
    def __len__(self):
        return len(self.source)
    def __getitem__(self, idx):
        source_data = self.source[idx]
        target_data = self.target[idx]
        return source_data, target_data

def heat_map_generation(encoder,decoder,batchsize,tf_ratio,cellType,bidirection):

    data3 = pre_processing_validation(copy.copy(test_input),copy.copy(test_output))

    dataset = MyDataset(data3["source_charToNum"],data3['val_charToNum'])
    dataLoader = DataLoader(dataset, batch_size=batchsize, shuffle=True)

    encoder.eval()
    decoder.eval()

    validation_accuracy = 0
    validation_loss = 0

    lossFunction = nn.NLLLoss()



    for batch_num, (sourceBatch, targetBatch) in enumerate(dataLoader):

        encoder_initial_state = encoder.getInitialState() #hiddenlayers * BatchSize * Neurons

        if(bidirection == "Yes"):
            reversed_batch = torch.flip(sourceBatch, dims=[1]) # reverse the batch across rows.
            sourceBatch = (sourceBatch + reversed_batch)//2 # adding reversed data to source data by averaging

        if(cellType == 'LSTM'):
            encoder_initial_state = (encoder_initial_state, encoder.getInitialState())

        encoderStates , encoderOutput = encoder(sourceBatch,encoder_initial_state)

        decoderCurrentState = encoderOutput # this selects the last state from encoder states

        encoderFinalLayerStates = encoderStates[:, -1, :, :]



        loss = 0 # decoder starts

        outputSeqLen = targetBatch.shape[1] # here you will get as name justified. 40

        Output = []
        #print(targetBatch)

        randNumber = random.random()

        for i in range(0,outputSeqLen):

            if(i == 0):
                decoderCurrentInput = torch.full((batchsize,1),0, device=device)
                #decoder_input_tensor = targetBatch[:, i].reshape(batchsize,1) #32*1
                #print(dec_input_tensor.shape)
            else:
                if randNumber < tf_ratio:
                    decoderCurrentInput = targetBatch[:, i].reshape(batchsize, 1)
                    #decoder_input_tensor = targetBatch[:, i].reshape(batchsize, 1) # current batch is passed
                else:
                    decoderCurrentInput = decoderCurrentInput.reshape(batchsize, 1)
                    #decoder_input_tensor = decoder_input_tensor.reshape(batchsize, 1) # prev result is passed

            decoderOutput, decoderCurrentState, attentionWeights = decoder(decoderCurrentInput, decoderCurrentState, encoderFinalLayerStates)

            for j in range (0,10):
                temp = []
                if(i<length[j]):
                    for k in range(0,30):
                        temp.append(attentionWeights[j][0][k].item())
                    attentions[j].append(temp)

            dummy, topi = decoderOutput.topk(1)

            decoderOutput = decoderOutput[:, -1, :]
            curr_target_chars = targetBatch[:, i] #(32)
            curr_target_chars = curr_target_chars.type(dtype=torch.long)
            loss+=(lossFunction(decoderOutput, curr_target_chars))

            decoderCurrentInput = topi.squeeze().detach()
            Output.append(decoderCurrentInput)

            # tensor_2d = torch.stack(Output)
            # Output = tensor_2d.t() #it is outside the for loop
        validation_loss += (loss.item()/outputSeqLen)

        break
        tensor_2d = torch.stack(Output)
        Output = tensor_2d.t()

        validation_accuracy += (Output == targetBatch).all(dim=1).sum().item()

        if(batch_num%40 == 0):
            print("bt:", batch_num, " loss:", loss.item()/outputSeqLen)
            #'k'/24
            # here you get the actual word letters seqeunces softamx indeces
            #[[0,1,2],[0,1,2]] = [shr,ram] 32*40
            #correct = (Output == targetBatch).all(dim=1).sum().item()
            #accuracy = accuracy + correct
    for i in range (0,10):
        for j in range (0,30):
            print(attentions[0][i][j])
    'l'/24
    encoder.train()
    decoder.train()
    print("validation_accuracy",validation_accuracy/40.96)
    print("validation_loss",validation_loss)
#     wandb.log({'validation_accuracy':validation_accuracy/40.96})
#     wandb.log({'validation_loss':validation_loss})

def validationAccuracy(encoder,decoder,batchsize,tf_ratio,cellType,bidirection):

    # Create a data loader for the validation set with the specified batch size
    dataLoader = dataLoaderFun("validation",batchsize) # dataLoader depending on train or validation

    # Set the encoder and decoder to evaluation mode
    encoder.eval()
    decoder.eval()

    # Initialize validation accuracy and loss to zero
    validation_accuracy = 0
    validation_loss = 0

    # Define the loss function as Negative Log Likelihood Loss
    lossFunction = nn.NLLLoss()

    # Iterate over each batch in the data loader
    for batch_num, (sourceBatch, targetBatch) in enumerate(dataLoader):
        #hiddenlayers * BatchSize * Neurons
        # Get the initial hidden state for the encoder
        encoder_initial_state = encoder.getInitialState()

        # If using bidirectional RNN, process the source batch accordingly
        if(bidirection != "No"):
            # Reverse the source batch along the sequence dimension
            reversed_batch = torch.flip(sourceBatch, dims=[1])
            # Average the original and reversed batches
            sourceBatch = (sourceBatch + reversed_batch)//2

        if(cellType == 'LSTM'):
             # If using LSTM, adjust the initial state for LSTM
            encoder_initial_state = (encoder_initial_state, encoder.getInitialState())

        # Pass the source batch through the encoder
        encoderStates , encoderOutput = encoder(sourceBatch,encoder_initial_state)

        # Initialize the decoder's current state with the encoder's output
        decoderCurrentState = encoderOutput

        # Get the final states of the encoder's layers
        encoderFinalLayerStates = encoderStates[:, -1, :, :]

        # List to store attention weights for analysis
        attentions = []

        loss = 0

        # Length of the output sequence (target sequence length)
        outputSeqLen = targetBatch.shape[1]

        Output = []

        # Generate a random number for teacher forcing decision
        randNumber = random.random()


        for i in range(0,outputSeqLen):

            if(i == 0):
                # For the first time step, use the start token as input
                decoderCurrentInput = torch.full((batchsize,1),0, device=device)
            else:
                if randNumber >= tf_ratio:
                    # Use the previous decoder output as input
                    decoderCurrentInput = decoderCurrentInput.reshape(batchsize, 1)
                else:
                    # Use the current target character (teacher forcing)
                    decoderCurrentInput = targetBatch[:, i].reshape(batchsize, 1)

             # Pass the current input and state through the decoder
            decoderOutput, decoderCurrentState, attentionWeights = decoder(decoderCurrentInput, decoderCurrentState, encoderFinalLayerStates)

            # Store the attention weights
            attentions.append(attentionWeights)
            dummy, topi = decoderOutput.topk(1)

            # Use the last time step's output for loss calculation
            decoderOutput = decoderOutput[:, -1, :]
            curr_target_chars = targetBatch[:, i] #(32)
            curr_target_chars = curr_target_chars.type(dtype=torch.long)
            loss+=(lossFunction(decoderOutput, curr_target_chars)) # Accumulate the loss for the current time step

            decoderCurrentInput = topi.squeeze().detach()
            Output.append(decoderCurrentInput)

        validation_loss += (loss.item()/outputSeqLen) # Accumulate the average loss for the current batch

        tensor_2d = torch.stack(Output)
        Output = tensor_2d.t()

        # Calculate and accumulate the accuracy for the current batch
        validation_accuracy += (Output == targetBatch).all(dim=1).sum().item()

        if(batch_num%40 == 0):
            print("bt:", batch_num, " loss:", loss.item()/outputSeqLen)
    # Set the encoder and decoder back to training mode
    encoder.train()
    decoder.train()
    #print("val_accuracy",validation_accuracy/4096)
    #print("val_loss",validation_loss)
    # wandb.log({'val_accuracy':validation_accuracy/4096})
    # wandb.log({'val_loss':validation_loss})

class Attention(nn.Module):
    def __init__(self, hiddenSize):
        super(Attention, self).__init__()
        self.Watt = nn.Linear(hiddenSize, hiddenSize)
        self.Uatt = nn.Linear(hiddenSize, hiddenSize)
        self.Vatt = nn.Linear(hiddenSize, 1)

    def forward(self, query, keys):
        calc = self.Watt(query) + self.Uatt(keys)
        scores = self.Vatt(torch.tanh(calc))
        scores = scores.squeeze().unsqueeze(1)
        weights = F.softmax(scores, dim=0)
        weights = weights.permute(2,1,0)
        keys = keys.permute(1,0,2)
        context = torch.bmm(weights, keys)
        return context, weights

class Encoder(nn.Module):

    def __init__(self,inputDim,embSize,encoderLayers,hiddenLayerNuerons,cellType,batch_size):
        super(Encoder, self).__init__()
        #Define embedding layer
        self.embedding = nn.Embedding(inputDim, embSize)
        self.encoderLayers = encoderLayers
        self.hiddenLayerNuerons = hiddenLayerNuerons
        self.batch_size = batch_size
        self.cellType = cellType
        # Initialize the appropriate RNN type based on cellType
        if(cellType=='GRU'):
            self.rnn = nn.GRU(embSize,hiddenLayerNuerons,num_layers=encoderLayers, batch_first=True)
        elif(cellType=='RNN'):
            self.rnn = nn.RNN(embSize,hiddenLayerNuerons,num_layers=encoderLayers, batch_first=True)
        else:
            self.rnn = nn.LSTM(embSize,hiddenLayerNuerons,num_layers=encoderLayers, batch_first=True)

    def forward(self,sourceBatch,encoderCurrState):
        # Get the sequence length from the source batch
        sequenceLength = len(sourceBatch[0])
        # Initialize tensor to store encoder states
        encoderStates = torch.zeros(sequenceLength,self.encoderLayers,self.batch_size,self.hiddenLayerNuerons,device=device)
        # Iterate over each time step in the sequence
        for i in range(0,sequenceLength):
            # Get the current input at time step i
            currInput = sourceBatch[:,i].reshape(self.batch_size,1)
            # Calculate the current states using the statesCalculation method
            dummy , encoderCurrState = self.statesCalculation(currInput,encoderCurrState)
            if(self.cellType != 'LSTM'):
                encoderStates[i] = encoderCurrState
            else:
                encoderStates[i] = encoderCurrState[1]

        # Return the encoder states and the current state of the encoder
        return encoderStates ,encoderCurrState


    def statesCalculation(self, currentInput, prevState):
        embdInput = self.embedding(currentInput) # Embed the current input
        # Pass the embedded input and previous state through the RNN
        output, prev_state = self.rnn(embdInput, prevState)
        return output, prev_state

    def getInitialState(self):
        # Return a tensor of zeros as the initial state
        return torch.zeros(self.encoderLayers,self.batch_size,self.hiddenLayerNuerons, device=device)

class Decoder(nn.Module):
    def __init__(self,outputDim,embSize,hiddenLayerNuerons,decoderLayers,cellType,dropout_p):
        super(Decoder, self).__init__()
        # Define embedding layer
        self.embedding = nn.Embedding(outputDim, embSize)
        self.cellType=cellType
        # Initialize the appropriate RNN type based on cellType
        #For GRU
        if(cellType == 'GRU'):
            self.rnn = nn.GRU(embSize+hiddenLayerNuerons,hiddenLayerNuerons,num_layers=decoderLayers, batch_first=True)
        #For RNN
        elif(cellType == 'RNN'):
            self.rnn = nn.RNN(embSize+hiddenLayerNuerons,hiddenLayerNuerons,num_layers=decoderLayers, batch_first=True)
        #For LSTM
        else:
            self.rnn = nn.LSTM(embSize+hiddenLayerNuerons,hiddenLayerNuerons,num_layers=decoderLayers, batch_first=True)

        #Used mapping to vocabulary
        # Define fully connected layer for output projection
        self.fc = nn.Linear(hiddenLayerNuerons, outputDim)
        self.softmax = nn.LogSoftmax(dim=2)
        self.dropout = nn.Dropout(dropout_p)
        # Initialize attention mechanism
        self.attention = Attention(hiddenLayerNuerons).to(device)

    def forward(self, current_input, prev_state,encoder_final_layers):
        # Compute context vector and attention weights
        if(self.cellType == 'LSTM'):
            context , attn_weights = self.attention(prev_state[1][-1,:,:], encoder_final_layers)
        else:
            context , attn_weights = self.attention(prev_state[-1,:,:], encoder_final_layers)
        # Embed the current input
        embd_input = self.embedding(current_input)
        curr_embd = F.relu(embd_input)
        #Input of GRU
        # Concatenate the embedded input and context vector
        input_gru = torch.cat((curr_embd, context), dim=2)
        output, prev_state = self.rnn(input_gru, prev_state)
        # Apply dropout to the output
        output = self.dropout(output)
        # Apply the fully connected layer and softmax to get the final output
        output = self.softmax(self.fc(output))
        return output, prev_state, attn_weights

def dataLoaderFun(dataName,batch_size):
    if(dataName == 'train'):
        dataset = MyDataset(data["source_charToNum"],data['val_charToNum'])
        return DataLoader(dataset, batch_size=batch_size, shuffle=True)
    else:
        dataset = MyDataset(data2["source_charToNum"],data2['val_charToNum'])
        return  DataLoader(dataset, batch_size=batch_size, shuffle=True)

def train(embSize,encoderLayers,decoderLayers,hiddenLayerNuerons,cellType,bidirection,dropout,epochs,batchsize,learningRate,optimizer,tf_ratio):
    # Add optimizer and teacher forcing ratio to wandb parameters

    # Initialize the data loader for the training data
    dataLoader = dataLoaderFun("train",batchsize) # dataLoader depending on train or validation

    encoder = Encoder(data["source_len"],embSize,encoderLayers,hiddenLayerNuerons,cellType,batchsize).to(device)
    decoder = Decoder(data["target_len"],embSize,hiddenLayerNuerons,encoderLayers,cellType,dropout).to(device)

    # Initialize the optimizer for the encoder and decoder
    if(optimizer == 'Adam'):
        encoderOptimizer = optim.Adam(encoder.parameters(), lr=learningRate)
        decoderOptimizer = optim.Adam(decoder.parameters(), lr=learningRate)
    else:
        encoderOptimizer = optim.NAdam(encoder.parameters(), lr=learningRate)
        decoderOptimizer = optim.NAdam(decoder.parameters(), lr=learningRate)

    # Define the loss function as Negative Log Likelihood Loss
    lossFunction = nn.NLLLoss()

    for epoch in range (0,epochs):

         # Initialize training accuracy and loss
        train_accuracy = 0
        train_loss = 0

        for batch_num, (sourceBatch, targetBatch) in enumerate(dataLoader):

            # Get the initial hidden state for the encoder
            encoderInitialState = encoder.getInitialState() #hiddenlayers * BatchSize * Neurons

            # Process the source batch if using bidirectional RNN
            if(bidirection == "Yes"):
                reversed_batch = torch.flip(sourceBatch, dims=[1]) # Reverse the source batch across the sequence dimension
                sourceBatch = (sourceBatch + reversed_batch)//2 # Average the original and reversed batches

            # Adjust the initial state for LSTM
            if(cellType == 'LSTM'):
                encoderInitialState = (encoderInitialState, encoder.getInitialState())

            # Pass the source batch through the encoder
            encoderStates,EcoderOutput= encoder(sourceBatch,encoderInitialState)

            # Get the final states of the encoder's layers
            encoderFinalLayerStates = encoderStates[:, -1, :, :] # this selects the hidden top layers from each sequence

            # Initialize the decoder's current state with the encoder's output
            decoderCurrentState = EcoderOutput
            attentions = []
            loss = 0 # decoder starts

            # Get the length of the output sequence
            outputSeqLen = targetBatch.shape[1]

            Output = []

            # Generate a random number for teacher forcing decision
            randNumber = random.random()

            # Iterate over each time step in the output sequence
            for i in range(0,outputSeqLen):

                if(i == 0):
                    # For the first time step, use the start token as input
                    decoderCurrentInput = torch.full((batchsize,1),0, device=device)
                else:
                    if randNumber >= tf_ratio:
                        # Use the previous decoder output as input
                        decoderCurrentInput = decoderCurrentInput.reshape(batchsize, 1)
                    else:
                        # Use the current target character (teacher forcing)
                        decoderCurrentInput = targetBatch[:, i].reshape(batchsize, 1)

                # Pass the current input and state through the decoder
                decoderOutput, decoderCurrentState, attentionWeights = decoder(decoderCurrentInput, decoderCurrentState, encoderFinalLayerStates)

                # Get the top prediction from the decoder output
                temporary, topIndeces = decoderOutput.topk(1)

                # Use the last time step's output for loss calculation
                decoderOutput = decoderOutput[:, -1, :]
                curr_target_chars = targetBatch[:, i]
                curr_target_chars = curr_target_chars.type(dtype=torch.long)
                loss+=(lossFunction(decoderOutput, curr_target_chars)) # Accumulate the loss for the current time step

                # Update the decoder input for the next time step
                decoderCurrentInput = topIndeces.squeeze().detach()
                Output.append(decoderCurrentInput)

                attentions.append(attentionWeights)

            # Stack the outputs and transpose to match the target batch shape
            tensor_2d = torch.stack(Output)
            Output = tensor_2d.t()
            train_accuracy += (Output == targetBatch).all(dim=1).sum().item()

            # Accumulate the average loss for the current batch
            train_loss += (loss.item()/outputSeqLen)

            # Zero the gradients for the optimizer
            encoderOptimizer.zero_grad()
            decoderOptimizer.zero_grad()
            #Backpropagation
            loss.backward()
            # Update the parameters
            encoderOptimizer.step()
            decoderOptimizer.step()

        #Log accuracies loss and wandb
        print("train_accuracy",train_accuracy/51200)
        print("train_loss",train_loss)
        wandb.log({'train_accuracy':train_accuracy/51200})
        wandb.log({'train_loss':train_loss})
        wandb.log({'epoch':epoch})
        validationAccuracy(encoder,decoder,batchsize,tf_ratio,cellType,bidirection)

def main_fun():
    wandb.init(project ='AttentionRNN')
    params = wandb.config
    with wandb.init(project = 'AttentionRNN', name='embedding'+str(params.embSize)+'cellType'+params.cellType+'batchSize'+str(params.batchsize)) as run:
        train(params.embSize,params.encoderLayers,params.decoderLayers,params.hiddenLayerNuerons,params.cellType,params.bidirection,params.dropout,params.epochs,params.batchsize,params.learningRate,params.optimizer,params.tf_ratio)

sweep_params = {
    'method' : 'bayes',
    'name'   : 'CS6910_assignment3_attention',
    'metric' : {
        'goal' : 'maximize',
        'name' : 'validation_accuracy',
    },
    'parameters' : {
        'embSize':{'values':[16,32,64]},
        'encoderLayers':{'values':[1,5,10]},
        'decoderLayers' : {'values' : [1,5,10]},
        'hiddenLayerNuerons'   : {'values' : [64,256,512]},
        'cellType' : {'values' : ['LSTM'] } ,
        'bidirection' : {'values' : ['no','Yes']},
        'dropout' : {'values' : [0,0.2,0.3]},
        'epochs'  : {'values': [10,15]},
        'batchsize' : {'values' : [32,64]},
        'learningRate' : {'values' : [1e-2,1e-3,1e-4]},
        'optimizer':{'values' : ['Adam','Nadam']},
        'tf_ratio' :{'values' : [0.2,0.4,0.5]}
    }
}
sweepId = wandb.sweep(sweep_params,project = 'AttentionRNN')
wandb.agent(sweepId,function =main_fun)
wandb.finish()

#Plotting heat map
#Plotting Hindi vs English words
import matplotlib.pyplot as plt
def plot_attention_heatmap(attention_matrix, input_sequence, output_sequence , id):

    plt.figure(figsize=(15, 10))

    ax = sns.heatmap(attention_matrix, cmap='viridis', annot=False, xticklabels=input_sequence, yticklabels=output_sequence)

    # Set font properties for Hindi characters
    font_path = '/kaggle/input/fonts-bro-1/NotoSansHindi-VariableFont_wdth,wght.ttf'  # Replace with the path to a Hindi font file
    hindi_font = FontProperties(fname=font_path)

    ax.set_xticklabels(input_sequence, fontproperties=hindi_font)
    ax.set_yticklabels(output_sequence, fontproperties=hindi_font)

    ax.set_xlabel('Input Sequence')
    ax.set_ylabel('Output Sequence')
    plt.title('Attention Heatmap')
    wandb.log({"Attention_Heatmap"+str(id)+ "temp": wandb.Image(plt)})

    plt.close()