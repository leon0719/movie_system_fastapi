from typing import Optional, List

from fastapi import HTTPException, APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from database import get_db
from models import post as model_post
from schemas import PostCreate, PostOut
import oauth2

router = APIRouter(prefix="/posts", tags=["Posts"])


def get_post_by_id(db: Session, post_id: int) -> model_post.Post:
    post = db.query(model_post.Post).filter(model_post.Post.id == post_id).first()
    return post


def check_post_owner(post: model_post.Post, current_user: int):
    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )


@router.get("/", response_model=List[PostOut])
def get_posts(
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
    limit: int = 10,
    skip: int = 0,
    search: Optional[str] = "",
):
    results = db.query(model_post.Post).all()
    return [{"post": post} for post in results]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostOut)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    new_post = model_post.Post(owner_id=current_user.id, **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return {"post": new_post}


@router.get("/{id}", response_model=PostOut)
def read_post(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    post = get_post_by_id(db, id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Post {id} not found"
        )
    return {"post": post}


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    post = get_post_by_id(db, id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Post {id} not found"
        )
    check_post_owner(post, current_user)
    db.delete(post)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{id}", response_model=PostOut)
def update_post(
    id: int,
    updated_post: PostCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user),
):
    post = get_post_by_id(db, id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Post {id} not found"
        )
    check_post_owner(post, current_user)
    for field, value in updated_post.dict().items():
        setattr(post, field, value)
    db.commit()
    db.refresh(post)
    return {"post": post}
