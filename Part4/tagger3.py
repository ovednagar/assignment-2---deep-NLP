import sys
sys.path.insert(0, "..")
from utils.nn_pref_suf_activator import PrefSufModelActivator
from utils.plotter import _plot_line
from utils.params import END
from utils.data_loader import TrainDataLoader, TestDataLoader
from utils.nn_activator import ModelActivator
from utils.nn_models import NeuralNet, PrefSufNet
import pickle


def _print_usage():
    print("\nOption1 - Train new model"
          "\n>> tagger1 --train   path_to_train_file   path_to_dev_file   num_epochs   model_name"
          "\n\nOption1 - Predict using existing model"
          "\n>> tagger1 --pred    path_to_test_file    model_name   out_file_name\n\n")


def _train_new_model(args):
        train_path = args[2]
        dev_path = args[3]
        num_epoch = int(args[4])
        model_name = args[5]
        import os
        pre_trained = os.path.join("..", "data", "word_embed", "wordVectors")
        dl_train = TrainDataLoader(train_path, suf_pref=True)
        dl_train.vocabulary.learn_distribution(dev_path, labeled=True)
        dl_dev = TrainDataLoader(dev_path, vocab=dl_train.vocabulary, suf_pref=True)

        voc_size = dl_train.vocab_size  # 100232
        pre_size = dl_train.vocabulary.len_pref()
        suf_size = dl_train.vocabulary.len_suf()
        embed_dim = 50
        out1 = int(dl_train.win_size * embed_dim * 0.66)
        out3 = int(dl_train.pos_dim)
        layers_dimensions = (dl_train.win_size, out1, out3)
        NN = PrefSufNet(layers_dimensions, voc_size, pre_size, suf_size, embedding_dim=embed_dim, pre_trained=pre_trained)
        activator = PrefSufModelActivator(NN, dl_train, dl_dev)
        loss_vec_dev, accuracy_vec_dev, loss_vec_train, accuracy_vec_train = activator.train(num_epoch)
        pickle.dump((loss_vec_dev, accuracy_vec_dev, loss_vec_train, accuracy_vec_train),
                    open("res_" + model_name, "wb"))
        _plot_line(loss_vec_dev, model_name + "_Dev - loss", "loss")
        _plot_line(loss_vec_train, model_name + "_Train - loss", "loss")
        _plot_line(accuracy_vec_dev, model_name + "_Dev - accuracy", "accuracy")
        _plot_line(accuracy_vec_train, model_name + "_Train - accuracy", "accuracy")
        pickle.dump((activator, dl_train.vocabulary, dl_train.pos_map), open(model_name, "wb"))


def _predict_existing_model(args):
    test_path = args[2]
    model_name = args[3]
    out_name = args[4]

    model_activator, vocabulary, pos_map = pickle.load(open(model_name, "rb"))

    dl_test = TestDataLoader(test_path, vocabulary, labeled=False, suf_pref=True)
    dl_test.vocabulary.learn_distribution(test_path, labeled=False)
    dl_test.load_pos_map(pos_map)
    res = model_activator.predict(dl_test)
    create_out_file(res, out_name)


def create_out_file(res, file_name):
    out_file = open(file_name, "wt")
    for word, pos in res:
        if word == END:
            continue
        out_file.write(word + " " + pos + "\n")
    out_file.close()


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 2:
        _print_usage()
        exit(1)
    job = args[1]
    if args[1] == "--train":
        if len(args) < 6:
            _print_usage()
            exit(1)
        _train_new_model(args)

    elif args[1] == "--pred":
        if len(args) < 5:
            _print_usage()
            exit(1)
        _predict_existing_model(args)
    else:
        _print_usage()
