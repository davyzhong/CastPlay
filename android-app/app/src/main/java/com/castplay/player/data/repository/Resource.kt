package com.castplay.player.data.repository

/**
 * 通用结果包装类
 *
 * 用于表示异步操作的状态和结果
 */
sealed class Resource<out T> {
    /**
     * 加载中状态
     */
    class Loading<T> : Resource<T>()

    /**
     * 成功状态
     */
    data class Success<T>(val data: T) : Resource<T>()

    /**
     * 错误状态
     */
    data class Error<T>(val message: String?, val data: T? = null) : Resource<T>()
}
