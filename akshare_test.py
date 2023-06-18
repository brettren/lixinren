import akshare as ak

index_investing_global_df = ak.index_investing_global_from_url(url="https://www.investing.com/indices/ftse-epra"
                                                                   "-nareit-hong-kong", period="每日",
                                                               start_date="19900101", end_date="20210909")
print(index_investing_global_df)
