"use server";

import { z } from "zod";

import { createRegisteredUser, getUser } from "@/lib/db/queries";

import { signIn } from "./auth";

const authFormSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});

export type LoginActionState = {
  status: "idle" | "in_progress" | "success" | "failed" | "invalid_data";
};

export const login = async (
  _: LoginActionState,
  formData: FormData
): Promise<LoginActionState> => {
  try {
    const validatedData = authFormSchema.parse({
      email: formData.get("email"),
      password: formData.get("password"),
    });

    await signIn("credentials", {
      email: validatedData.email,
      password: validatedData.password,
      redirect: false,
    });

    return { status: "success" };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { status: "invalid_data" };
    }

    return { status: "failed" };
  }
};

export type RegisterActionState = {
  status:
    | "idle"
    | "in_progress"
    | "success"
    | "failed"
    | "user_exists"
    | "invalid_data";
  data: {
    user?: {
      id: string;
      email: string;
      role: "user";
    };
  } | null;
  msg: string;
};

const registerFormSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
  fullName: z.string().trim().min(2),
});

export const register = async (
  _: RegisterActionState,
  formData: FormData
): Promise<RegisterActionState> => {
  try {
    const validatedData = registerFormSchema.parse({
      email: formData.get("email"),
      password: formData.get("password"),
      fullName: formData.get("fullName"),
    });

    const normalizedEmail = validatedData.email.trim().toLowerCase();
    const [user] = await getUser(normalizedEmail);

    if (user) {
      return {
        status: "user_exists",
        data: null,
        msg: "账号已存在",
      };
    }

    const createdUser = await createRegisteredUser({
      email: normalizedEmail,
      password: validatedData.password,
      fullName: validatedData.fullName,
    });

    await signIn("credentials", {
      email: normalizedEmail,
      password: validatedData.password,
      redirect: false,
    });

    return {
      status: "success",
      data: {
        user: {
          id: createdUser.id,
          email: createdUser.email,
          role: createdUser.role,
        },
      },
      msg: "注册成功",
    };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        status: "invalid_data",
        data: null,
        msg: "参数校验失败",
      };
    }

    return {
      status: "failed",
      data: null,
      msg: "注册失败",
    };
  }
};
