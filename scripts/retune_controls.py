"""Hand-labelled developer controls. Not a held-out evaluation or dictionary sources."""
from core import digest

def controls():
    # Labels were written before any new API call. No source definition is reused in publication.
    examples=[
      ('memory','Memory is the ability to encode, retain and retrieve information.','Memory is the capacity to store and recall information.',True,True,'cognition'),
      ('authoritative parenting','Authoritative parenting is characterized by high levels of both parental control and warmth.','Authoritative parenting is marked by high parental control together with warmth.',True,True,'development'),
      ('DBT','Dialectical Behavior Therapy (DBT) is a psychotherapy developed by Marsha Linehan that teaches skills for regulating emotion.','DBT stands for Dialectical Behavior Therapy, a psychotherapy developed by Marsha Linehan to teach emotion-regulation skills.',True,True,'counselling skills'),
      ('diencephalic amnesia','Diencephalic amnesia is memory impairment associated with injury to diencephalic brain structures.','Diencephalic amnesia is a memory impairment linked to damage in diencephalic brain structures.',True,True,'biological'),
      ('lightness constancy','Lightness constancy is the tendency to perceive a surface as having stable lightness despite changes in illumination.','Lightness constancy is perceiving the lightness of a surface as relatively stable when illumination changes.',True,True,'cognition'),
      ('moderator','A moderator is a variable that changes the strength or direction of the relation between two other variables.','In research, a moderator changes the strength or direction of a relationship between two variables.',True,True,'research methods'),
      ('receptivity','In this 1902 account, receptivity is the capacity of the mind to receive impressions.','In this historical account, receptivity denotes the mind’s capacity to receive impressions.',True,True,'history'),
      ('-phobia','The combining form -phobia denotes fear or aversion.','The suffix -phobia denotes fear or aversion.',True,True,'mental health'),
      ('MCS','MCS denotes a multicarotenoid supplement tested for its effects on skin pigmentation.','MCS is a measure of emotional distress.',False,False,'assessment'),
      ('census','The Middle Atlantic census division consists of New Jersey, New York and Pennsylvania.','A census is a complete enumeration of a population.',False,False,'research methods'),
      ('working memory','Working memory scores correlated with age in our sample. The study did not define working memory.','Working memory stores and manipulates information over a short period.',False,False,'cognition'),
      ('moderator','A forum moderator removes spam and enforces community rules.','A moderator changes the strength of a relationship between research variables.',False,False,'research methods'),
      ('-phobia','Participants with social phobia completed a questionnaire.','The suffix -phobia denotes fear or aversion.',False,False,'mental health'),
      ('memory','Memory is the ability to retain and retrieve information.','Memory is an ability that permanently preserves every experienced event without error.',True,False,'cognition'),
      ('anxiety','Anxiety is a state of apprehension in anticipation of a possible future threat.','For anxiety, take two tablets daily.',True,False,'mental health'),
      ('threshold theory','This exercise-biology threshold theory says moderate exercise promotes muscular adaptation and excessive exercise causes cellular damage.','Threshold theory explains sensory detection in psychology.',False,False,'biological'),
      ('ribosome','A ribosome is a cellular structure that synthesizes proteins.','A ribosome is a protein-producing cell structure.',False,True,'biological'),
      ('vermis','The cerebellar vermis is the midline portion of the cerebellum and contributes to coordination of posture and movement.','The vermis is the midline part of the cerebellum involved in coordinating posture and movement.',True,True,'biological'),
      ('receptivity','A 1902 theory described receptivity as receiving mental impressions, and claimed that mind was passive in this process.','Modern neuroscience has established that all minds are passive receivers of impressions.',True,False,'history'),
    ]
    examples += [
      ('memory','Memory is the ability to retain and retrieve information. In this study, memory was operationalized as recall of a 20-word list after five minutes.','In this study, memory refers to recall of a 20-word list after five minutes.',True,False,'cognition'),
      ('memory','Memory is the ability to retain and retrieve information. The study found better recall after sleep.','Memory retains and retrieves information. The study found better recall after sleep.',True,False,'cognition'),
      ('memory','Memory is the ability to retain and retrieve information. This experiment operationalized memory as recall of a 20-word list after five minutes.','Memory is recall of a 20-word list after five minutes.',True,False,'cognition'),
    ]
    rows=[]
    for i,(term,text,definition,fit,read,field) in enumerate(examples):
        p={'term':term,'source':'developer-authored-control','source_record':str(i),'revision':'1','text':text};p['packet_hash']=digest(p)
        rows.append({'id':f'control-{i:02d}','packet':p,'definition':definition,'field':field,'expected_fit':fit,'expected_read':read})
    return rows
