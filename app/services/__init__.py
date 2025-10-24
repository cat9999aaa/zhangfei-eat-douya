"""服务层模块"""

from .gemini_service import (
    generate_article_with_gemini,
    generate_visual_blueprint,
    build_visual_prompts,
    summarize_paragraph_for_image,
    test_gemini_model,
    get_available_models
)

from .image_service import (
    download_unsplash_image,
    download_pexels_image,
    download_pixabay_image,
    get_local_image_by_tags,
    list_local_images,
    list_uploaded_images,
    test_unsplash_connection,
    test_pexels_connection,
    test_pixabay_connection
)

from .comfyui_service import (
    generate_image_with_comfyui,
    update_comfyui_runtime,
    test_comfyui_workflow
)

from .document_service import (
    create_word_document,
    list_generated_documents
)

from .task_service import (
    create_generation_task,
    get_task_status,
    retry_failed_topics_in_task,
    create_executor,
    initialize_executor
)

__all__ = [
    'generate_article_with_gemini',
    'generate_visual_blueprint',
    'build_visual_prompts',
    'summarize_paragraph_for_image',
    'test_gemini_model',
    'get_available_models',
    'download_unsplash_image',
    'download_pexels_image',
    'download_pixabay_image',
    'get_local_image_by_tags',
    'list_local_images',
    'list_uploaded_images',
    'test_unsplash_connection',
    'test_pexels_connection',
    'test_pixabay_connection',
    'generate_image_with_comfyui',
    'update_comfyui_runtime',
    'test_comfyui_workflow',
    'create_word_document',
    'list_generated_documents',
    'create_generation_task',
    'get_task_status',
    'retry_failed_topics_in_task',
    'create_executor',
    'initialize_executor'
]
