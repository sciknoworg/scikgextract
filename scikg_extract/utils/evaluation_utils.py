from typing import Dict, List

import evaluate
from transformers import AutoTokenizer, PreTrainedTokenizer
from sentence_transformers import SentenceTransformer, util


def rouge_score(references: list, predictions: list) -> dict:
    """
    Calculate the ROUGE scores between the reference output and the predicted output
    Args:
        references (list): The list of reference outputs
        predictions (list): The list of predicted outputs
    Returns:
        dict: The ROUGE score
    """
    rouge = evaluate.load("rouge")
    return rouge.compute(predictions=predictions, references=references)


def bleu_score(references: list, predictions: list) -> dict:
    """
    Calculate the BLEU scores between the reference output and the predicted output
    Args:
        references (list): The list of reference outputs
        predictions (list): The list of predicted outputs
    Returns:
        dict: The BLEU score
    """
    bleu = evaluate.load("bleu")
    return bleu.compute(predictions=predictions, references=references)


def split_into_chunks(text: str, tokenizer: PreTrainedTokenizer, max_length: int = 512) -> list:
    """
    Split the input text into chunks based on the tokenizer and max length
    Args:
        text (str): The input text to be split
        tokenizer (PreTrainedTokenizer): The tokenizer to be used for splitting
        max_length (int): The maximum length of each chunk
    Returns:
        list: The list of text chunks
    """
    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks = [
        tokens[i : i + max_length - 4] for i in range(0, len(tokens), max_length - 4)
    ]
    return [tokenizer.decode(chunk, skip_special_tokens=False) for chunk in chunks]


def bert_score(references: list, predictions: list, embedding_model: str, embedding_model_revision: str, max_length: int = 512) -> dict:
    """
    Calculate the BERT scores between the reference output and the predicted output
    Args:
        references (list): The list of reference outputs
        predictions (list): The list of predicted outputs
        embedding_model (str): The name of the embedding model to be used
        embedding_model_revision (str): The revision of the embedding model to be used
        max_length (int): The maximum length of each chunk
    Returns:
        dict: The BERT score
    """
    # Loading the BERT score and Embedding model from HuggingFace
    bertscore = evaluate.load("bertscore")
    tokenizer = AutoTokenizer.from_pretrained(
        embedding_model, revision=embedding_model_revision  # nosec B615
    )

    # Intializing dictionary for storing intermediate scores
    scores: Dict[str, List[float]] = {"precision": [], "recall": [], "f1": []}

    # Iterating each reference and prediction pair
    for pred, ref in zip(predictions, references):
        pred_chunks = split_into_chunks(pred, tokenizer, max_length)
        ref_chunks = split_into_chunks(ref, tokenizer, max_length)

        # Calculating bert score for each chunk separately
        for p_chunk, r_chunk in zip(pred_chunks, ref_chunks):
            result = bertscore.compute(
                predictions=[p_chunk],
                references=[r_chunk],
                model_type=embedding_model,
                lang="en",
            )
            scores["precision"].append(result["precision"][0])
            scores["recall"].append(result["recall"][0])
            scores["f1"].append(result["f1"][0])

    # Aggregating the scores - average across chunks
    scores_avg = {
        "precision": sum(scores["precision"]) / len(scores["precision"]),
        "recall": sum(scores["recall"]) / len(scores["recall"]),
        "f1": sum(scores["f1"]) / len(scores["f1"]),
    }
    return scores_avg

def cosine_similarity_score(references: list, predictions: list, embedding_model: str, max_length: int = 512) -> dict:
    """
    Calculate the Cosine Similarity scores between the reference output and the predicted output
    Args:
        references (list): The list of reference outputs
        predictions (list): The list of predicted outputs
        embedding_model (str): The name of the embedding model to be used
        max_length (int): The maximum length of each chunk
    Returns:
        dict: The Cosine Similarity score
    """
    # Loading the Embedding model from Sentence Transformers
    model = SentenceTransformer(embedding_model)

    # Intializing list for storing similarity scores
    similarity_scores: List[float] = []

    # Iterating each reference and prediction pair
    for pred, ref in zip(predictions, references):
        pred_chunks = split_into_chunks(pred, model.tokenizer, max_length)
        ref_chunks = split_into_chunks(ref, model.tokenizer, max_length)

        # Calculating cosine similarity for each chunk separately
        for p_chunk, r_chunk in zip(pred_chunks, ref_chunks):
            emb1 = model.encode(p_chunk, convert_to_tensor=True)
            emb2 = model.encode(r_chunk, convert_to_tensor=True)
            cosine_score = util.cos_sim(emb1, emb2).item()
            similarity_scores.append(cosine_score)

    # Aggregating the scores - average across chunks
    average_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
    return average_similarity