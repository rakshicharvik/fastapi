from sqlalchemy import Column, Integer, String, ForeignKey, Double 
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class JobBoard(Base):
  __tablename__ = 'job_boards'
  id = Column(Integer, primary_key=True)
  slug = Column(String, nullable=False, unique=True)
  logo_url = Column(String, nullable=True)
  
class JobPost(Base):
  __tablename__ = 'posts'
  id = Column(Integer, primary_key=True)
  title = Column(String,nullable=False)
  salary = Column(Double,nullable=False)
  job_board_id = Column(Integer, ForeignKey("job_boards.id"), nullable=False)
  job_board = relationship("JobBoard")
  
 