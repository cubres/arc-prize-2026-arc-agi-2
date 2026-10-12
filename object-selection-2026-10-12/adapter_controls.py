"""Owned invented native-pair controls, no pool/model/ARC task execution."""
import native_overlay


def main():
    demo1=[[0,2,2,0,3],[0,2,2,0,0],[0,0,0,0,0]]
    demo2=[[0,4,4,4,0,5],[0,4,4,4,0,0],[0,0,0,0,0,0]]
    query=[[0,7,7,0,8],[0,7,7,0,0],[0,0,0,0,0]]
    task={"train":[{"input":demo1,"output":[[2,2],[2,2]]},
                   {"input":demo2,"output":[[4,4,4],[4,4,4]]}],
          "test":[{"input":query}]}
    full=[[[[1]],[[2]]]]
    result,_=native_overlay.fill_query_pairs(task,full)
    assert result==full
    duplicate=[[[[1]],[[1]]]]
    result,_=native_overlay.fill_query_pairs(task,duplicate)
    assert result==duplicate
    # A legitimate [[0]] remains a populated first attempt.
    pair=[[[[0]]]]
    result,receipt=native_overlay.fill_query_pairs(task,pair)
    assert result[0][0]==[[0]] and result[0][1]==[[7,7],[7,7]]
    assert receipt["new_guesses"]==1
    result,receipt=native_overlay.fill_query_pairs(task,[[]])
    assert result[0][0]==[[7,7],[7,7]] and receipt["new_guesses"]>=1
    print("PASS 5 native-pair controls: full/duplicate/zero/one/empty slots")


if __name__=="__main__":
    main()
