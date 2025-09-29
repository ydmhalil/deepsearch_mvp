from rag import main as rag_main


def generate_report(index_path, meta_path, query, out_path):
    rag_main(index_path, meta_path, query, out_path)


if __name__ == '__main__':
    generate_report('./data/faiss.index', './data/meta.pkl', 'fırlatma kontrol', './data/report.txt')
    print('Done')
