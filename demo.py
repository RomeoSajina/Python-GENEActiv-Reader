from gene_activ import GENEActiv

if __name__ == "__main__":

    ga = GENEActiv("example/left_ankle_example.bin")

    print("Raw data: ", ga.raw)
    print("Processed data: ", ga.data)
    
    ga.aggregate("1s").plot()
